#!/usr/bin/env python3 

from rich.console import Console
from rich.table import Table, box
import boto3
import os
from colorama import Fore,Back,Style,init
import argparse

init(autoreset=True)

profile = os.environ.get("AWS_PROFILE", "default")
session = boto3.Session(profile_name=profile)
ec2 = None 

def list_ami(profile="Default"):

    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client("ec2")
        response = ec2.describe_images(Owners=['self', 'amazon', 'aws-marketplace'])
    except Exception as e:
        print(f"{Fore.RED}Connexion à EC2 impossible : {e}")
        return()

    images = response['Images']
    
    for image in images:
        ami_id = image.get('ImageId')
        name = image.get('Name')
        description = image.get('Description', 'N/A')
        owner_id = image.get('OwnerId')
        creation_date = image.get('CreationDate')

        yield((ami_id, name, description, owner_id, creation_date))

def print_table(result):
    console = Console()
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, show_lines=False)

    table.add_column("AMI ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Description", style="white")
    table.add_column("Owner ID", style="cyan")
    table.add_column("Creation Date", style="yellow")

    for aid,name,desc,oid,date in result: 
        table.add_row(aid,name,desc,oid,date)

    console.print(table)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Lister les AMI")
    parser.add_argument('-g', '--grep', type=str, default=None, help='Filtre expression réguliere sur la description')
    parser.add_argument('-o', '--owner', type=int, default=None, help='Idenfiant owner de l\'AMI')
    args = parser.parse_args()

    result=list_ami()

    if (args.owner):
        result = [
            (aid, name, desc, oid, date)
            for aid, name, desc, oid, date in result
            if oid == args.owner
        ]

    if args.grep:
        result = [
            (aid, name, desc, oid, date)
            for aid, name, desc, oid, date in result
            if re.search(args.grep, desc)
        ]

    print_table(result)


