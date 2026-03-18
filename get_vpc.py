#!/usr/bin/env python3

import boto3
import argparse
from rich.table import Table, box
from rich.console import Console

console = Console()

def list_vpcs(ec2):
    table = Table(box=box.SIMPLE_HEAVY, header_style="yellow")
    table.add_column("VPC ID", style="cyan")
    table.add_column("CIDR")
    table.add_column("State", style="green")
    table.add_column("Name")

    for vpc in ec2.vpcs.all():
        name = next((t['Value'] for t in (vpc.tags or []) if t['Key'] == 'Name'), "N/A")
        table.add_row(vpc.id, vpc.cidr_block, vpc.state, name)
    console.print(table)

def get_vpc_details(ec2, vpc_id):
    try:
        vpc = ec2.Vpc(vpc_id)
        console.print(f"\n[purple]###### Inventaire du VPC: {vpc_id} ######[/purple]\n")
        console.print(f"  [bold]ID[/bold]      : {vpc.id}")
        console.print(f"  [bold]CIDR[/bold]    : {vpc.cidr_block}")
        console.print(f"  [bold]State[/bold]   : {vpc.state}")
        
        # Sous-réseaux
        subnets = list(vpc.subnets.all())
        if subnets:
            console.print("\n  [bold]Sous-réseaux associés :[/bold]\n")
            for sub in subnets:
                console.print(f"    - {sub.id} ({sub.cidr_block}) en {sub.availability_zone}")
        
        # Tables de routage
        console.print("\n  [bold]Tables de routage :[/bold]\n")
        for rt in vpc.route_tables.all():
            main_str = " (Main)" if any(assoc.main for assoc in rt.associations) else ""
            console.print(f"    - {rt.id}{main_str}")
            for route in rt.routes:
                dest = route.destination_cidr_block or route.destination_ipv6_cidr_block or "Local"
                target = (route.gateway_id or route.nat_gateway_id or route.network_interface_id or 
                          route.instance_id or route.vpc_peering_connection_id or "Local")
                console.print(f"        {dest} -> {target}")

        # Internet Gateways
        igws = list(vpc.internet_gateways.all())
        if igws:
            console.print("\n  [bold]Internet Gateways :[/bold]\n")
            for igw in igws:
                console.print(f"    - {igw.id}")

        # Elastic IPs (associées aux instances du VPC via des interfaces réseau)
        console.print("\n  [bold]Elastic IPs (EIPs) :[/bold]\n")
        found_eip = False
        for eni in vpc.network_interfaces.all():
            if eni.association and eni.association.public_ip:
                console.print(f"    - {eni.association.public_ip} (associée à {eni.id})")
                found_eip = True
        if not found_eip:
            console.print("    - Aucune EIP trouvée.")
                
    except Exception as e:
        console.print(f"[red]Erreur : VPC {vpc_id} non trouvé. {e}[/red]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outil d'inventoring VPC AWS")
    parser.add_argument('--profile', help="Profile AWS")
    parser.add_argument('--region', help="Région AWS")
    parser.add_argument('vpc', nargs='?', help="ID du VPC à inventorier")

    args = parser.parse_args()
    
    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    ec2 = session.resource('ec2', region_name=args.region) if args.region else session.resource('ec2')

    if args.vpc: 
        get_vpc_details(ec2, args.vpc)
    else:
        list_vpcs(ec2)
