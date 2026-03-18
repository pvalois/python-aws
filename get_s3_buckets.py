#!/usr/bin/env python3

import boto3
from rich.table import Table,box
from rich.console import Console
import humanize
from aws_local import client

s3 = client("s3")
buckets = s3.list_buckets()

table = Table(box=box.SIMPLE_HEAVY)
table.add_column("Name", style="cyan", no_wrap=True)
table.add_column("Creation Time", style="magenta")
table.add_column("Region", style="green")
table.add_column("Files", justify="right")
table.add_column("Size", justify="right")

buckets_list=sorted(buckets.get("Buckets", []), key=lambda x: x["CreationDate"], reverse=True)

for bucket in buckets_list: 
    nom = bucket["Name"]
    date_form = str(bucket["CreationDate"])
    region = bucket.get("BucketRegion") or s3.get_bucket_location(Bucket=nom).get("LocationConstraint") or "us-east-1"

    objets = s3.list_objects_v2(Bucket=nom)
    nb_fichiers = objets.get('KeyCount', 0)
    taille_octets = 0

    if 'Contents' in objets:
        taille_octets = sum(obj.get('Size', 0) for obj in objets['Contents'])

    table.add_row(nom, date_form, region, str(nb_fichiers), humanize.naturalsize(taille_octets))

console = Console()
console.print(table)
