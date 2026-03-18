#!/usr/bin/env python3
from aws_local import client
from rich.table import Table, box
from rich.console import Console
import humanize

console = Console()

# --- Créer le client S3 ---
s3 = client("s3")

# --- Lister les buckets ---
buckets = s3.list_buckets().get("Buckets", [])

for bucket in buckets:
    bucket_name = bucket["Name"]
    total_size = 0

    # Lister les objets du bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    objects = response.get("Contents", [])

    table = Table(title=f"Bucket: {bucket_name}", box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Key", style="white", justify="center")
    table.add_column("Size", style="white", justify="right")
    table.add_column("Last Modified", style="cyan")
    table.add_column("Storage Class", style="yellow")

    for obj in objects:
        key = obj["Key"]
        size = obj["Size"]
        lastmod = str(obj["LastModified"])
        storage = obj.get("StorageClass", "STANDARD")
        table.add_row(key, f"{size:,}", lastmod, storage)
        total_size += size

    table.caption = (
        f"Taille totale : {total_size:,} octets "
        f"({humanize.naturalsize(total_size, binary=True)})"
    )

    console.print(table)
    console.print()

