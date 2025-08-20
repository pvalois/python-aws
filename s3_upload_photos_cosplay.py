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

cpt=0
for root,dirs,files in os.walk('/export/Photos/Shootings/Conventions/2018-07-05 - Japan Expo/'):
  for file in files:
    cpt=cpt+1
    if (cpt>20): break
    fullpath=os.path.join(root,file)
    ext=file.split(".")[1]
    tname='{0:4d}.'.format(cpt)+ext
    tname=tname.strip()
    if (cpt<10): tname="0"+tname
    if (cpt<100): tname="0"+tname
    print ("Uploading",file,"as",tname)
    s3.upload_file(fullpath,"test",tname)
