#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from rich.table import Table, box
from rich.console import Console

def main():
    parser = argparse.ArgumentParser(description="Lister les tables de routage AWS avec détection de sortie Internet")
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "default"), help="Profil AWS")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION"), help="Région AWS")
    args = parser.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        ec2 = session.client("ec2")
        resp = ec2.describe_route_tables()
    except (BotoCoreError, ClientError) as e:
        print(f"Erreur connexion AWS : {e}")
        return

    console = Console()
    table = Table(box=box.SIMPLE_HEAVY, header_style="bold white on blue")

    table.add_column("Route Table ID", style="bold cyan")
    table.add_column("Type", justify="center")
    table.add_column("Destination", style="bold yellow")
    table.add_column("Target")
    table.add_column("State")
    table.add_column("Main", justify="center")
    table.add_column("Name")

    for rt in resp.get("RouteTables", []):
        rt_id = rt.get("RouteTableId")
        routes = rt.get("Routes", [])
        
        # Détection du type de table (Publique si 0.0.0.0/0 vers une IGW)
        is_public = any(r.get('DestinationCidrBlock') == '0.0.0.0/0' and 'GatewayId' in r and r['GatewayId'].startswith('igw-') for r in routes)
        rt_type = "[bold green]PUBLIC[/]" if is_public else "[bold white on red]PRIVATE[/]"
        
        # Détection Main Table
        is_main = "[bold green]Yes[/]" if any(assoc.get("Main") for assoc in rt.get("Associations", [])) else "No"
        
        # Tag Name
        name = next((t["Value"] for t in rt.get("Tags", []) if t["Key"] == "Name"), "-")

        for i, route in enumerate(routes):
            dest = route.get("DestinationCidrBlock") or route.get("DestinationIpv6CidrBlock") or "PrefixList"
            state = route.get("State", "active")
            
            # Coloration de la cible
            target = "Unknown"
            target_keys = ['GatewayId', 'NatGatewayId', 'InstanceId', 'VpcPeeringConnectionId', 'NetworkInterfaceId']
            for key in target_keys:
                if key in route:
                    target = route[key]
                    break
            
            target_display = f"[bold green]{target}[/]" if target == "local" or target.startswith("igw-") else f"[yellow]{target}[/]"

            if i == 0:
                table.add_row(rt_id, rt_type, dest, target_display, state, is_main, name)
            else:
                table.add_row("", "", dest, target_display, state, "", "")
        
        table.add_section() # Ligne de séparation entre les tables

    console.print(table)

if __name__ == "__main__":
    main()
