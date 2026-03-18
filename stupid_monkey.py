#!/usr/bin/env python3 

import random
import os
from aws_local import client

ec2 = client("ec2")

def chaos_monkey(lab_name, min_stop=1, max_stop=3, action='stop'):
    """
    Chaos monkey qui arrête ou termine un nombre aléatoire d'instances dans un lab.
    
    :param lab_name: Nom du lab (tag Lab)
    :param min_stop: Nombre minimum de VMs à affecter
    :param max_stop: Nombre maximum de VMs à affecter
    :param action: 'stop' ou 'terminate'
    """

    instances = []
    filters = [{'Name': 'instance-state-name', 'Values': ['running']},
               {'Name': 'tag:Lab', 'Values': [lab_name]}
              ]
    response = ec2.describe_instances(Filters=filters)

    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instances.append(instance['InstanceId'])

    if not instances:
        print(f"Aucune instance running trouvée dans le lab {lab_name}")
        return
    
    n = random.randint(min_stop, min(max_stop, len(instances)))
    targets = random.sample(instances, n)
    
    print(f"Chaos monkey : on {action} {n} instances dans le lab {lab_name}")
    for instance in targets:
        print(f"{action.capitalize()} instance {instance}")
        if action == 'stop':
            ec2.stop_instances(InstanceIds=targets)
        elif action == 'terminate':
            ec2.terminate_instances(InstanceIds=targets)
        else:
            print(f"Action inconnue : {action}")

if __name__ == "__main__":
    ec2 = client("ec2")
    chaos_monkey('lab1', min_stop=1, max_stop=2, action='stop')

