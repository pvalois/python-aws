#!/usr/bin/env python3

import argparse
import sys
from aws_local import client
from rich.console import Console

console = Console()

def is_elbv2_available():
    """Teste si l'API ELBv2 est accessible."""
    try:
        c = client("elbv2")
        c.describe_load_balancers(PageSize=1)
        return True
    except Exception:
        return False

def check_ingress(security_group_id, source_ip, port):
    """Vérifie si une règle autorise le trafic."""
    ec2 = client("ec2")
    try:
        sgs = ec2.describe_security_groups(GroupIds=[security_group_id])
        for sg in sgs.get('SecurityGroups', []):
            for rule in sg.get('IpPermissions', []):
                from_port = rule.get('FromPort')
                to_port = rule.get('ToPort')
                # Vérification port et IP
                port_match = (from_port is None) or (from_port <= port <= to_port)
                ip_match = any(r.get('CidrIp') == source_ip or r.get('CidrIp') == '0.0.0.0/0' 
                               for r in rule.get('IpRanges', []))
                if port_match and ip_match:
                    return True
    except:
        return False
    return False

def trace(instance_id, source_ip, port):
    elbv2_ok = is_elbv2_available()
    console.print(f"[bold cyan]Tracing ingress path to: {instance_id}[/]")
    ec2 = client("ec2")
    
    try:
        inst_data = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        
        # Trace conditionnelle ELB
        if elbv2_ok:
            console.print("Internet ──> [bold green]Load Balancer (Active)[/]")
        else:
            console.print("Internet ──> [bold yellow]Load Balancer (N/A - License)[/]")
            
        console.print(f"           └──> [bold white]VPC / Subnet[/] ({inst_data.get('SubnetId')})")
        
        for eni in inst_data.get('NetworkInterfaces', []):
            eni_id = eni['NetworkInterfaceId']
            console.print(f"                └──> [bold yellow]ENI:[/] {eni_id}")
            
            for sg in eni.get('Groups', []):
                sg_id = sg['GroupId']
                status = "[bold green]ALLOWED"
                if source_ip and port:
                    status = "[bold green]ALLOWED" if check_ingress(sg_id, source_ip, port) else "[bold red]BLOCKED"
                
                console.print(f"                     └──> [bold cyan]SG:[/] {sg_id} -> {status}")
        
        console.print(f"                          └──> [bold green]Instance:[/] {instance_id}")

    except Exception as e:
        console.print(f"[bold red]ERR: {str(e)}[/]")

def main():
    parser = argparse.ArgumentParser(description="Trace ingress path with conditional API checks")
    parser.add_argument("instance_id", help="Instance ID (i-...)")
    parser.add_argument("-s", "--source", help="IP source")
    parser.add_argument("-d", "--port", type=int, help="Port")
    args = parser.parse_args()
    
    if not args.instance_id.startswith("i-"):
        console.print("[bold red]Erreur:[/bold red] L'ID doit commencer par 'i-'.")
        sys.exit(1)
        
    trace(args.instance_id, args.source, args.port)

if __name__ == "__main__":
    main()
