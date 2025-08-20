#!/usr/bin/env python3
import os
import boto3
from botocore.client import Config
from configlocator import *
from rich.table import Table, box
from rich.console import Console
import humanize

config=configlocator("aws_s3.ini")

c=config['pepiniere']
endpoint=c['endpoint']
access_key=c['access_key_id']
secret=c['access_key_secret']
region=c['region']

s3 = boto3.resource('s3',
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret,
                    config=Config(signature_version='s3v4'),
                    region_name=region)

for bucket in s3.buckets.all():
    count = sum(1 for _ in bucket.objects.all())
    console=Console()

    table = Table(title=f"bucket: {bucket.name}",box=box.MINIMAL, show_lines=False)

    table.add_column("Key", style="white", justify="center")
    table.add_column("Size", style="white", justify="right")
    table.add_column("Last Modified", style="cyan")
    table.add_column("Storage Class", style="yellow")

    total_size=0 

    for obj in bucket.objects.all():
        key=f"{obj.key}"
        size=f"{obj.size:,}"
        lastmod=f"{obj.last_modified}"
        storage=f"{obj.storage_class}"
        table.add_row(key,size,lastmod,storage)
        total_size += obj.size

    table.caption = (
        f"Taille totale : {total_size:,} octets"
        f" ({humanize.naturalsize(total_size, binary=True)})"
    )

    console.print(table)
