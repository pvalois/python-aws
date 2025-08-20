#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

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

    for sn in resp.get("Subnets", []):
        subnet_id = sn.get("SubnetId")
        cidr = sn.get("CidrBlock")
        az = sn.get("AvailabilityZone")
        vpc = sn.get("VpcId")
        name = "-"
        if "Tags" in sn:
            for t in sn["Tags"]:
                if t["Key"] == "Name":
                    name = t["Value"]
        print(f"{subnet_id}\t{cidr}\t{az}\t{vpc}\t{name}")

if __name__ == "__main__":
    main()

