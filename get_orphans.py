#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import argparse
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE_HEAVY

# Estimations FinOps (Prix moyens mensuels)
PRICES = {
    "EIP": 3.60,      
    "EBS": 0.10,      
    "SNAP": 0.05,     
    "ALB": 18.00      
}

def get_eip_orphans(ec2_c):
    data = []
    try:
        addrs = ec2_c.describe_addresses().get('Addresses', [])
        for eip in addrs:
            if not eip.get('InstanceId') and not eip.get('NetworkInterfaceId'):
                name = next((t['Value'] for t in eip.get('Tags', []) if t['Key'] == 'Name'), "-")
                data.append([eip.get('PublicIp'), eip.get('AllocationId'), name])
    except: pass
    return data

def get_eni_orphans(ec2_c):
    data = []
    try:
        enis = ec2_c.describe_network_interfaces().get('NetworkInterfaces', [])
        for eni in enis:
            if eni.get('Status') != 'in-use':
                name = next((t['Value'] for t in eni.get('Tags', []) if t['Key'] == 'Name'), "-")
                data.append([eni.get('NetworkInterfaceId'), eni.get('PrivateIpAddress'), eni.get('VpcId'), name])
    except: pass
    return data

def get_vol_orphans(ec2_r):
    data = []
    try:
        for v in ec2_r.volumes.filter(Filters=[{'Name': 'status', 'Values': ['available']}]):
            name = next((t['Value'] for t in v.tags or [] if t['Key'] == 'Name'), "-")
            data.append([v.id, v.size, v.volume_type, name])
    except: pass
    return data

def get_snap_orphans_safe(ec2_r, ec2_c):
    """Détecte UNIQUEMENT les snapshots sans volume ET sans aucune AMI rattachée."""
    data = []
    try:
        # 1. On liste tous les snapshots utilisés par TOUTES les AMIs (même les publiques si besoin, mais ici 'self')
        amis = ec2_c.describe_images(Owners=['self'])['Images']
        snaps_in_amis = set()
        for ami in amis:
            for bdm in ami.get('BlockDeviceMappings', []):
                if 'Ebs' in bdm and 'SnapshotId' in bdm['Ebs']:
                    snaps_in_amis.add(bdm['Ebs']['SnapshotId'])

        # 2. On filtre les snapshots
        for s in ec2_r.snapshots.filter(OwnerIds=['self']):
            # Vérifier si le snapshot est dans une AMI
            if s.id in snaps_in_amis:
                continue
            
            # Vérifier si le volume source existe encore
            try:
                ec2_r.Volume(s.volume_id).load()
                continue # Le volume existe, on ne touche pas
            except:
                # Si on est ici : Pas d'AMI associée ET pas de volume source
                name = next((t['Value'] for t in s.tags or [] if t['Key'] == 'Name'), "-")
                data.append([s.id, s.volume_size, s.start_time.strftime("%Y-%m-%d"), name])
    except: pass
    return data

def get_lb_orphans(elbv2_c):
    data = []
    try:
        lbs = elbv2_c.describe_load_balancers()['LoadBalancers']
        tgs = elbv2_c.describe_target_groups()['TargetGroups']
        for lb in lbs:
            arn = lb['LoadBalancerArn']
            lb_tgs = [tg for tg in tgs if arn in tg.get('LoadBalancerArns', [])]
            
            active = False
            for tg in lb_tgs:
                health = elbv2_c.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
                if health['TargetHealthDescriptions']:
                    active = True
                    break
            
            if not active:
                data.append([lb['LoadBalancerName'], lb['Type'], lb['LoadBalancerArn']])
    except: pass
    return data

def generate_scripts(eips, enis, vols, snaps, lbs, profile):
    folder = f"scripts-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    os.makedirs(folder, exist_ok=True)
    p = f"--profile {profile}" if profile else ""
    
    files = {
        "clean_ips.sh": [f"aws ec2 release-address {p} --allocation-id {r[1]}" for r in eips],
        "clean_enis.sh": [f"aws ec2 delete-network-interface {p} --network-interface-id {r[0]}" for r in enis],
        "clean_volumes.sh": [f"aws ec2 delete-volume {p} --volume-id {r[0]}" for r in vols],
        "clean_snapshots.sh": [f"aws ec2 delete-snapshot {p} --snapshot-id {r[0]}" for r in snaps],
        "clean_lbs.sh": [f"aws elbv2 delete-load-balancer {p} --load-balancer-arn {r[2]}" for r in lbs]
    }

    for name, cmds in files.items():
        if cmds:
            path = os.path.join(folder, name)
            with open(path, "w") as f:
                f.write("#!/bin/bash\n" + "\n".join(cmds) + "\n")
            os.chmod(path, 0o755)
    return folder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--profile', default='default')
    parser.add_argument('--scripts', action='store_true')
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    ec2_c, ec2_r, elbv2_c = session.client('ec2'), session.resource('ec2'), session.client('elbv2')
    console = Console()

    with console.status("[bold green]Scan en cours..."):
        eips = get_eip_orphans(ec2_c)
        enis = get_eni_orphans(ec2_c)
        vols = get_vol_orphans(ec2_r)
        snaps = get_snap_orphans_safe(ec2_r, ec2_c)
        lbs = get_lb_orphans(elbv2_c)

    console.print(f"\n[bold white on red] AUDIT CLEANER - {args.profile} [/]\n", justify="center")

    total = 0
    groups = [
        (eips, "IPs Publiques", "yellow", ["IP", "ID", "Name"], lambda r: PRICES["EIP"]),
        (vols, "Volumes EBS", "red", ["ID", "GiB", "Type", "Name"], lambda r: r[1] * PRICES["EBS"]),
        (enis, "Interfaces ENI", "cyan", ["ID", "Private", "VPC", "Name"], lambda r: 0),
        (snaps, "Snapshots 100% Orphelins", "magenta", ["ID", "GiB", "Date", "Name"], lambda r: r[1] * PRICES["SNAP"]),
        (lbs, "Load Balancers Vides", "blue", ["Nom", "Type", "ARN"], lambda r: PRICES["ALB"])
    ]

    for data, title, color, cols, cost_f in groups:
        table = Table(box=SIMPLE_HEAVY, title=f"[bold {color}]{title}[/]", header_style=f"bold {color}")
        for c in cols: table.add_column(c)
        table.add_column("Saving/Mo", justify="right")
        for row in data:
            s = cost_f(row)
            total += s
            table.add_row(*[str(x) for x in row], f"${s:.2f}")
        console.print(table)

    console.print(f"\n[bold green]ÉCONOMIE TOTALE : ${total:.2f}/mois[/]")

    if args.scripts:
        path = generate_scripts(eips, enis, vols, snaps, lbs, args.profile)
        console.print(f"[bold cyan]Scripts générés dans ./{path}[/]\n")

if __name__ == "__main__":
    main()
