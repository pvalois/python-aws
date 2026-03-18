#!/usr/bin/env python3
import os
from aws_local import client

s3 = client("s3")
buckets = s3.list_buckets()

try:
  filename=sys.argv[1]
except:
  exit(0)

bucket="test"
s3.upload_file(filename,bucket,file)
