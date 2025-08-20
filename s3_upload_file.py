#!/usr/bin/env python3
import os
import boto3
from botocore.client import Config
from configlocator import *

config=configlocator("aws_s3.ini")

c=config['pepiniere']
endpoint=c['endpoint']
access_key=c['access_key_id']
secret=c['access_key_secret']
region=c['region']

s3 = boto3.client('s3',
                  endpoint_url=endpoint,
                  aws_access_key_id=access_key,
                  aws_secret_access_key=secret,
                  config=Config(signature_version='s3v4'),
                  region_name=region)

try:
  filename=sys.argv[1]
except:
  exit(0)

bucket="test"
s3.upload_file(filename,bucket,file)
