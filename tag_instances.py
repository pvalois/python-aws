#!/usr/bin/env python3

import argparse 
import boto3
import os

profile = os.environ.get("AWS_PROFILE", "default")
session = boto3.Session(profile_name=profile)
ec2=None

def tag_instance(instance_id, key, value, dry_run=False):
    print  (f"Tag apply on {instance_id} : {key}={value}")
    if not dry_run: 
        instance = ec2.Instance(instance_id)
        instance.create_tags(Tags=[{'Key': key, 'Value': value}])

if __name__ == "__main__" :

    parser = argparse.ArgumentParser(description="Gestion des toggles")
    parser.add_argument('-k', '--key', required=True, help='Clef à ajouter')
    parser.add_argument('-v', '--value', required=True, help='Valeur à stocker dans la clef')
    parser.add_argument('--dry-run', action='store_true', help="Simule l'execution sans changer quoi que ce soit")
    parser.add_argument('instances', nargs='*', help="Liste d'instances à tagguer")

    args = parser.parse_args()
    ec2 = session.resource('ec2')

    if (not args.dry_run): 
        try:
            any(ec2.instances.limit(1))
        except Exception as e:
            print("Connexion à EC2 impossible :", e)
            exit(1)

    for _id in args.instances:
        tag_instance(_id,args.key,args.value,dry_run=args.dry_run)
