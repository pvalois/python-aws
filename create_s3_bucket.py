#!/usr/bin/env python3

import sys
import time
import botocore
from aws_local import client
from rich.table import Table, box
from rich.console import Console
import humanize

console = Console()
s3 = client("s3")

try:
  bucket_name = sys.argv[1]
except: 
  print ("please add the bucket name to create")
  exit(1)

def bucket_exists(name):
    try:
        s3.head_bucket(Bucket=name)
        return True
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket", "NotFound"):
            return False
        raise

def wait_for_bucket(name, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        if bucket_exists(name):
            return True
        time.sleep(0.5)
    return False

try:
    region = getattr(s3.meta, "region_name", None)
except Exception:
    region = None

created = False

try:
    if region in (None, "", "us-east-1"):
        # us-east-1 : ne pas fournir LocationConstraint
        s3.create_bucket(Bucket=bucket_name)
    else:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region}
        )
    created = True
    print(f"Bucket '{bucket_name}' : create_bucket() success.")
except botocore.exceptions.ClientError as e:
    errcode = e.response.get("Error", {}).get("Code", "")
    errmsg = e.response.get("Error", {}).get("Message", str(e))

    if errcode in ("IllegalLocationConstraintException",):
        try:
            s3.create_bucket(Bucket=bucket_name)
            created = True
            print(f"Bucket '{bucket_name}' créé (retry sans LocationConstraint).")
        except botocore.exceptions.ClientError as e2:
            err2 = e2.response.get("Error", {}).get("Code", "")
            if err2 in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                print(f"Bucket '{bucket_name}' existe déjà (owned).")
                created = True
            else:
                print(f"Erreur création bucket (retry): {e2}")
                raise
    elif errcode in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
        print(f"Bucket '{bucket_name}' existe déjà (owned).")
        created = True
    else:
        print(f"Erreur création bucket: {errcode} - {errmsg}")
        raise


if not created:
    print("Le bucket n'a pas pu être créé. Abandon.")
    raise exit(1)

if not wait_for_bucket(bucket_name, timeout=15):
    print(f"Le bucket '{bucket_name}' n'est pas joignable après attente. Abandon.")
    raise exit(1)

