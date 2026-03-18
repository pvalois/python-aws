#!/usr/bin/env python3

import sys
from aws_local import client

try:
    bucket_name=sys.argv[1]
except:
    print ("Must profide a bucket name")
    exit(1)

s3 = client("s3")
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name)

for page in pages:
    objects = page.get("Contents", [])
    
    if not objects:
        continue

    for obj in objects:
        print(f"Deleting {obj['Key']}")

    delete_list = {'Objects': [{'Key': obj['Key']} for obj in objects]}
    s3.delete_objects(Bucket=bucket_name, Delete=delete_list)

print("Done")

