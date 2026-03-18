#!/usr/bin/env python3

import argparse 
import boto3
import os

profile = os.environ.get("AWS_PROFILE", "default")
session = boto3.Session(profile_name=profile)
ec2=None

def tag_instances(instance_ids, key, value, dry_run=False):
    print(f"Tag APPLY on {len(instance_ids)} instances: {key}={value}")
    if not dry_run:
        ec2.create_tags(Resources=instance_ids, Tags=[{'Key': key, 'Value': value}])

def detag_instances(instance_ids, key, dry_run=False):
    print(f"Tag REMOVE on {len(instance_ids)} instances: {key}")
    if not dry_run:
        ec2.meta.client.delete_tags(Resources=instance_ids, Tags=[{'Key': key}])

if __name__ == "__main__" :

    parser = argparse.ArgumentParser(description="Gestion des toggles")
    parser.add_argument('-k', '--key', required=True, help='Clef à ajouter/supprimer')
    parser.add_argument('-v', '--value', help='Valeur à stocker dans la clef')
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

    print (args.key,args.key[-1])

    if (args.key.endswith("-")):
        detag_instances(args.instances,args.key[:-1],dry_run=args.dry_run)
    else:
        if (args.value):
            tag_instances(args.instances,args.key,args.value,dry_run=args.dry_run)
        else:
            print ("Key sans Value. Exiting")

