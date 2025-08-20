#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import csv
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def parse_args():
    p = argparse.ArgumentParser(
        description="Lister les volumes EBS du compte/région (avec filtres simples)."
    )
    p.add_argument("--profile", default=os.environ.get("AWS_PROFILE") or os.environ.get("profile") or "default",
                   help="Profil AWS (default: %(default)s)")
    p.add_argument("--region", default=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
                   help="Région AWS (ex: eu-west-1). Par défaut: celle du profil/config.")
    p.add_argument("--state", choices=["creating","available","in-use","deleting","deleted","error"],
                   help="Filtrer par état du volume EBS.")
    p.add_argument("--json", action="store_true", help="Sortie JSON.")
    p.add_argument("--csv", metavar="PATH", help="Écrit la liste en CSV au chemin donné.")
    return p.parse_args()

def get_ec2_client(profile, region):
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        return session.client("ec2")
    except (BotoCoreError, ClientError) as e:
        print(f"Erreur de session/credentials: {e}", file=sys.stderr)
        sys.exit(1)

def list_volumes(client, state=None):
    filters = []
    if state:
        filters.append({"Name": "status", "Values": [state]})
    try:
        paginator = client.get_paginator("describe_volumes")
        params = {"Filters": filters} if filters else {}
        for page in paginator.paginate(**params):
            for v in page.get("Volumes", []):
                yield v
    except (BotoCoreError, ClientError) as e:
        print(f"Erreur describe_volumes: {e}", file=sys.stderr)
        sys.exit(2)

def simplify(volume):
    attachments = [
        {
            "InstanceId": a.get("InstanceId"),
            "Device": a.get("Device"),
            "State": a.get("State")
        }
        for a in volume.get("Attachments", [])
    ]
    tags = {t["Key"]: t["Value"] for t in volume.get("Tags", [])} if volume.get("Tags") else {}
    return {
        "VolumeId": volume.get("VolumeId"),
        "State": volume.get("State"),
        "SizeGiB": volume.get("Size"),
        "VolumeType": volume.get("VolumeType"),
        "Iops": volume.get("Iops"),
        "Throughput": volume.get("Throughput"),
        "Encrypted": volume.get("Encrypted"),
        "KmsKeyId": volume.get("KmsKeyId"),
        "AvailabilityZone": volume.get("AvailabilityZone"),
        "MultiAttachEnabled": volume.get("MultiAttachEnabled"),
        "SnapshotId": volume.get("SnapshotId"),
        "CreateTime": volume.get("CreateTime").isoformat() if volume.get("CreateTime") else None,
        "Attachments": attachments,
        "Tags": tags,
    }

def print_human(rows):
    if not rows:
        print("Aucun volume trouvé.")
        return
    # En-tête
    header = [
        "VolumeId", "State", "SizeGiB", "Type", "AZ", "Encrypted", "AttachedTo", "Tags"
    ]
    print("\t".join(header))
    for r in rows:
        attached = ",".join([a["InstanceId"] for a in r["Attachments"]]) if r["Attachments"] else "-"
        tags = ",".join(f'{k}={v}' for k,v in r["Tags"].items()) if r["Tags"] else "-"
        line = [
            r["VolumeId"] or "",
            r["State"] or "",
            str(r["SizeGiB"] or ""),
            r["VolumeType"] or "",
            r["AvailabilityZone"] or "",
            str(r["Encrypted"]),
            attached,
            tags
        ]
        print("\t".join(line))

def write_csv(path, rows):
    fieldnames = list(rows[0].keys()) if rows else []
    # Aplatis attachments/tags pour CSV simple
    flat_rows = []
    for r in rows:
        flat = r.copy()
        flat["Attachments"] = ",".join([a["InstanceId"] for a in r["Attachments"]]) if r["Attachments"] else ""
        flat["Tags"] = ",".join(f'{k}={v}' for k,v in r["Tags"].items()) if r["Tags"] else ""
        flat_rows.append(flat)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=flat_rows[0].keys() if flat_rows else fieldnames)
        writer.writeheader()
        for row in flat_rows:
            writer.writerow(row)

def main():
    args = parse_args()
    client = get_ec2_client(args.profile, args.region)
    vols = [simplify(v) for v in list_volumes(client, state=args.state)]

    if args.csv:
        write_csv(args.csv, vols)
        print(f"CSV écrit: {args.csv}")

    if args.json:
        print(json.dumps(vols, ensure_ascii=False, indent=2))
    elif not args.csv:
        print_human(vols)

if __name__ == "__main__":
    main()

