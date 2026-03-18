#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE_HEAVY

# --- CONFIGURATION ---
FALLBACK_PRICES = {
    "EIP": 3.66,      # $0.005/hr
    "EBS_GB": 0.10,   
    "SNAP_GB": 0.05,  
    "ALB": 16.42
}

def get_unit_costs(ce_client):
    """Récupère les prix réels du client pour l'affichage des gains potentiels."""
    prices = {"EBS": (FALLBACK_PRICES["EBS_GB"], True), "SNAP": (FALLBACK_PRICES["SNAP_GB"], True)}
    try:
        today = datetime.now(timezone.utc).date()
        start = (today - timedelta(days=32)).replace(day=1).isoformat()
        end = today.replace(day=1).isoformat()
        r = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start, 'End': end},
            Granularity='MONTHLY', Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}]
        )
        for group in r.get('ResultsByTime', [])[0].get('Groups', []):
            utype, cost, qty = group['Keys'][0], float(group['Metrics']['UnblendedCost']['Amount']), float(group['Metrics']['UsageQuantity']['Amount'])
            if qty > 0:
                if "EBS:VolumeUsage" in utype: prices["EBS"] = (cost/qty, False)
                elif "EBS:SnapshotUsage" in utype: prices["SNAP"] = (cost/qty, False)
    except: pass
    return prices

def get_orphans(session):
    ec2_c = session.client('ec2')
    ec2_r = session.resource('ec2')
    elbv2 = session.client('elbv2')
    
    # 1. EIPs
    eips = []
    for e in ec2_c.describe_addresses().get('Addresses', []):
        if not e.get('InstanceId') and not e.get('NetworkInterfaceId'):
            name = next((t['Value'] for t in e.get('Tags', []) if t['Key'] == 'Name'), "-")
            eips.append([e.get('PublicIp'), e.get('AllocationId'), name])
            
    # 2. Volumes Available
    vols = []
    for v in ec2_r.volumes.filter(Filters=[{'Name': 'status', 'Values': ['available']}]):
        name = next((t['Value'] for t in v.tags or [] if t['Key'] == 'Name'), "-")
        vols.append([v.id, v.size, name])

    # 3. Snapshots (Vraiment orphelins : pas de volume, pas d'AMI)
    snaps = []
    amis = ec2_c.describe_images(Owners=['self'])['Images']
    snaps_in_amis = {bdm['Ebs']['SnapshotId'] for a in amis for bdm in a.get('BlockDeviceMappings', []) if 'Ebs' in bdm}
    
    for s in ec2_r.snapshots.filter(OwnerIds=['self']):
        if s.id in snaps_in_amis: continue
        try:
            ec2_r.Volume(s.volume_id).load()
        except:
            name = next((t['Value'] for t in s.tags or [] if t['Key'] == 'Name'), "-")
            snaps.append([s.id, s.volume_size, name])

    return eips, vols, snaps

def generate_cleanup_scripts(directory, eips, vols, snaps, profile):
    if not os.path.exists(directory):
        os.makedirs(directory)
    p = f"--profile {profile}" if profile else ""
    
    scripts = {
        "clean_eips.sh": [f"aws ec2 release-address {p} --allocation-id {r[1]}" for r in eips],
        "clean_volumes.sh": [f"aws ec2 delete-volume {p} --volume-id {r[0]}" for r in vols],
        "clean_snapshots.sh": [f"aws ec2 delete-snapshot {p} --snapshot-id {r[0]}" for r in snaps]
    }
    
    for name, cmds in scripts.items():
        if cmds:
            path = os.path.join(directory, name)
            with open(path, "w") as f:
                f.write("#!/bin/bash\n" + "\n".join(cmds) + "\n")
            os.chmod(path, 0o755)
    return len(scripts)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--profile', default='default')
    parser.add_argument('-o', '--output', help="Répertoire de sortie (déclenche la création des scripts)")
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    console = Console()
    region = session.region_name or "us-east-1"

    with console.status(f"[bold green]Audit des ressources inutilisées ({region})..."):
        prices = get_unit_costs(session.client('ce'))
        eips, vols, snaps = get_orphans(session)

    console.print(f"\n[bold white on red] AUDIT ORPHELINS - {args.profile} [/]\n", justify="center")

    p_ebs, fb_ebs = prices["EBS"]
    p_snap, fb_snap = prices["SNAP"]
    total_saving = 0

    # Affichage Volumes
    t_vol = Table(box=SIMPLE_HEAVY, title=f"Volumes à supprimer (@{p_ebs:.3f}/GB)", header_style="bold red")
    t_vol.add_column("ID"); t_vol.add_column("Taille"); t_vol.add_column("Gain/Mois", justify="right")
    for v in vols:
        gain = v[1] * p_ebs
        total_saving += gain
        t_vol.add_row(v[0], f"{v[1]}GB", f"${gain:.2f}")
    console.print(t_vol)

    # Affichage Snapshots
    t_snap = Table(box=SIMPLE_HEAVY, title=f"Snapshots à supprimer (@{p_snap:.3f}/GB)", header_style="bold yellow")
    t_snap.add_column("ID"); t_snap.add_column("Taille"); t_snap.add_column("Gain/Mois", justify="right")
    for s in snaps:
        gain = s[1] * p_snap
        total_saving += gain
        t_snap.add_row(s[0], f"{s[1]}GB", f"${gain:.2f}")
    console.print(t_snap)

    console.print(f"\n[bold green]ÉCONOMIE MENSUELLE POTENTIELLE : ${total_saving:.2f}[/]")
    if fb_ebs or fb_snap:
        console.print("[dim red](Note: Certains calculs utilisent des prix par défaut/FALLBACK)[/]")

    if args.output:
        generate_cleanup_scripts(args.output, eips, vols, snaps, args.profile)
        console.print(f"\n[bold cyan]SCRIPTS DE NETTOYAGE GÉNÉRÉS DANS : {args.output}[/]\n")

if __name__ == "__main__":
    main()
