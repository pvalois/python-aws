#!/usr/bin/env python3

import boto3
import os

profile = os.environ.get("AWS_PROFILE", "default")
session = boto3.Session(profile_name=profile)
ec2 = session.resource("ec2")

try:
  any(ec2.instances.limit(1))
except Exception as e:
  print (f"Erreur: {e}")
  exit(1)

ec2info = {}

for instance in ec2.instances.all():
    name = 'N/A'
    if instance.tags:
        for tag in instance.tags:
            if tag['Key'] == 'Name':
                name = tag['Value']
                break

    # Add instance info to a dictionary
    ec2info[instance.id] = {
        'Name': name,
        'Type': instance.instance_type,
        'State': instance.state['Name'],
        'Private IP': instance.private_ip_address,
        'Public IP': instance.public_ip_address,
    }

attributes = ['Name', 'Type', 'State', 'Private IP', 'Public IP', 'Launch Time']

for instance_id, instance in ec2info.items():
    for key in attributes:
        print("{0}: {1}".format(key, instance[key]))
    print("------")
