#!/usr/bin/env python3 

from aws_local import client

ec2 = client("ec2")

filters = [{'Name': 'instance-state-name', 'Values': ['stopped']}]
response = ec2.describe_instances(Filters=filters)

instance_ids = []
for reservation in response.get('Reservations', []):
    for instance in reservation.get('Instances', []):
        instance_ids.append(instance['InstanceId'])

if not instance_ids:
    print("Aucune instance à l'arrêt trouvée.")
    exit(0)

print(f"Démarrage des instances : {', '.join(instance_ids)}")
ec2.start_instances(InstanceIds=instance_ids)




