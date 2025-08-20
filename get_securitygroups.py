#!/usr/bin/env python3

import boto3
import argparse

def list_security_groups(ec2):
    sgs = ec2.security_groups.all()
    for sg in sgs:
        print(f"{sg.group_id} | {sg.group_name} | VPC: {sg.vpc_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lister tous les Security Groups")
    parser.add_argument('--profile', help="Nom du profile AWS à utiliser", default=None)
    parser.add_argument('--region', help="Région AWS", default=None)
    args = parser.parse_args()

    session_args = {}
    if args.profile:
        session_args['profile_name'] = args.profile
    session = boto3.Session(**session_args)

    ec2_args = {}
    if args.region:
        ec2_args['region_name'] = args.region

    ec2 = session.resource('ec2', **ec2_args)
    
    try:
      list_security_groups(ec2)
    except Exception as e: 
      print (f"Erreur : {e}")

