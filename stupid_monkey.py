#!/usr/bin/env python3 

import random
import boto3
import os

profile = os.environ.get("AWS_PROFILE", "default")
session = boto3.Session(profile_name=profile)
ec3 = None

def chaos_monkey(lab_name, min_stop=1, max_stop=3, action='stop'):
    """
    Chaos monkey qui arrête ou termine un nombre aléatoire d'instances dans un lab.
    
    :param lab_name: Nom du lab (tag Lab)
    :param min_stop: Nombre minimum de VMs à affecter
    :param max_stop: Nombre maximum de VMs à affecter
    :param action: 'stop' ou 'terminate'
    """
    instances = list(ec2.instances.filter(
        Filters=[{'Name': 'tag:Lab', 'Values': [lab_name]}, {'Name': 'instance-state-name', 'Values': ['running']}]
    ))
    
    if not instances:
        print(f"Aucune instance running trouvée dans le lab {lab_name}")
        return
    
    n = random.randint(min_stop, min(max_stop, len(instances)))
    targets = random.sample(instances, n)
    
    print(f"Chaos monkey : on {action} {n} instances dans le lab {lab_name}")
    for instance in targets:
        print(f"{action.capitalize()} instance {instance.id}")
        if action == 'stop':
            instance.stop()
        elif action == 'terminate':
            instance.terminate()
        else:
            print("Action inconnue :", action)

# Exemple d'exécution
if __name__ == "__main__":
    ec3 = session.resource('ec2')

    try:
        any(ec3.instances.limit(1))
    except Exception as e:
        print("Connexion à EC2 impossible :", e)
        exit(1)

    chaos_monkey('lab1', min_stop=1, max_stop=2, action='stop')

