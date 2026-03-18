#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from rich.table import Table, box
from rich.console import Console

def main():
    parser = argparse.ArgumentParser(description="Lister les subnets AWS")
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "default"),
                        help="Profil AWS (default: %(default)s)")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION"),
                        help="Région AWS (ex: eu-west-1)")
    args = parser.parse_args()

    try:
        session = boto3.Session(profile_name=args.profile, region_name=args.region)
        ec2 = session.client("ec2")
        resp = ec2.describe_subnets()
    except (BotoCoreError, ClientError) as e:
        print(f"Erreur connexion AWS : {e}")
        return

    table = Table(box=box.SIMPLE_HEAVY)

    table.add_column("Subnet ID", style="bold cyan")
    table.add_column("CIDR", style="bold yellow")
    table.add_column("Availability Zone", style="bold green")
    table.add_column("VPC ID")
    table.add_column("Name")

    for sn in resp.get("Subnets", []):
        subnet_id = sn.get("SubnetId",None)
        cidr = sn.get("CidrBlock")
        az = sn.get("AvailabilityZone")
        vpc = sn.get("VpcId")
        name = sn.get("Name","")
        if "Tags" in sn:
            for t in sn["Tags"]:
                if t["Key"] == "Name":
                    name = t["Value"]


        table.add_row(subnet_id,cidr,az,vpc,name)

    console = Console()
    console.print(table)

if __name__ == "__main__":
    main()

