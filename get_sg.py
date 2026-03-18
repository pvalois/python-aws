#!/usr/bin/env python3

import boto3
import argparse
from rich.text import Text
from rich.table import Table, box
from rich.console import Console

console=Console()

def get_security_group(ec2, sg_identifier):
    try:
        # On cherche soit par ID (sg-xxx), soit par Nom
        if sg_identifier.startswith('sg-'):
            filters = [{'Name': 'group-id', 'Values': [sg_identifier]}]
        else:
            filters = [{'Name': 'group-name', 'Values': [sg_identifier]}]
        
        groups = list(ec2.security_groups.filter(Filters=filters))
        
        if not groups:
            print(f"Aucun Security Group trouvé pour '{sg_identifier}'")
            return

        if len(groups)>1:
            print (f"Plusieurs groupes trouvés pour '{sg_identifier}'")
            print ()
            for g in groups: 
                print (f" -- {g.group_id}")
            return 

        sg = groups[0]

        infos = Text.assemble(
            ("  Name           : ", "bold"), (f"{sg.group_name}\n", "white"),
            ("  Description    : ", "bold"), (f"{sg.description}\n", "italic"),
            ("\n"),
            ("  Security Group : ", "bold"), (f"{sg.group_id}\n", "cyan"),
            ("  VPC ID         : ", "bold"), (f"{sg.vpc_id}", "green"),
        )

        ingress=get_rules(sg.ip_permissions)
        egress=get_rules(sg.ip_permissions_egress)

        table = Table(box=box.SIMPLE, header_style="yellow")
        table.add_column ("Ports", style="cyan")
        table.add_column ("Protocol", style="cyan")
        table.add_column ("Direction", style="white")
        table.add_column ("Target", style="green")

        for ports, proto, target in ingress:
            table.add_row (ports, proto, "INGRESS", target)

        for ports, proto, target in egress:
            table.add_row (ports, proto, "EGRESS", target)

        console.print()

        console.print("  [purple]###### Informations Générales ######")
        console.print()
        console.print(infos)
        console.print()

        console.print("  [purple]###### Ingress/Egress rules ######")
        console.print(table)

    except Exception as e:
        print(f"Erreur lors de la récupération du groupe : {e}")

def get_rules(permissions):
    if not permissions:
        return []

    ruleset=[]
    for rule in permissions:
        proto = rule.get('IpProtocol')
        proto_display = "ANY" if proto == "-1" else proto
        
        from_port = rule.get('FromPort', 'ANY')
        to_port = rule.get('ToPort', 'ANY')
        port_range = f"{from_port}:{to_port}" if from_port != 'ANY' else "ANY"

        targets = []

        for ip in rule.get('IpRanges', []):
            targets.append(ip.get('CidrIp'))

        for ip6 in rule.get('Ipv6Ranges', []):
            targets.append(ip6.get('CidrIpv6'))

        for group in rule.get('UserIdGroupPairs', []):
            targets.append(f"SG: {group.get('GroupId')}")
            
        target_str = "\n".join(targets) if targets else "N/A"
        ruleset.append((port_range, proto_display, target_str))
    
    return(ruleset)

def list_security_groups(ec2):
    sgs = ec2.security_groups.all()

    table = Table(box=box.SIMPLE_HEAVY, header_style="yellow")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("VPC")

    for sg in sgs:
        table.add_row(sg.group_id, sg.group_name, sg.vpc_id)

    console.print(table)
    console.print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lister tous les Security Groups")
    parser.add_argument('--profile', help="Nom du profile AWS à utiliser", default=None)
    parser.add_argument('--region', help="Région AWS", default=None)
    parser.add_argument("sg", nargs="?", help="Nom du security group à consulter", default=None)
    args = parser.parse_args()

    session_args = {}
    if args.profile:
        session_args['profile_name'] = args.profile
    session = boto3.Session(**session_args)

    ec2_args = {}
    if args.region:
        ec2_args['region_name'] = args.region

    ec2 = session.resource('ec2', **ec2_args)

    if (args.sg):
        get_security_group(ec2,args.sg)
        exit(0)
    
    try:
      list_security_groups(ec2)
    except Exception as e: 
      print (f"Erreur : {e}")

