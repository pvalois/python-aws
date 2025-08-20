#!/usr/bin/env python3 

import boto3

for i in ec2.instances.all():
    if i.state['Name'] == 'stopped':
        i.start()





