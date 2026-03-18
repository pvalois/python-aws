#!/usr/bin/env python3

import json
from aws_local import client

def get_tags_string(resource):
    """Extrait les tags d'une ressource et les formate en string."""
    tags = resource.get('Tags', [])
    if not tags: return ""
    if isinstance(tags, list):
        tag_list = [f"{t.get('Key')}={t.get('Value')}" for t in tags if 'Key' in t]
        return f" [{', '.join(sorted(tag_list))}]"
    return ""

def get_inventory():
    # Format : (service, méthode, clé_racine, clé_id, nom_affichage)
    checks = [
        # --- NETWORK ---
        ("ec2", "describe_vpcs", "Vpcs", "VpcId", "vpcs"),
        ("ec2", "describe_subnets", "Subnets", "SubnetId", "subnets"),
        ("ec2", "describe_security_groups", "SecurityGroups", "GroupId", "security_groups"),
        ("ec2", "describe_internet_gateways", "InternetGateways", "InternetGatewayId", "internet_gateways"),
        ("ec2", "describe_route_tables", "RouteTables", "RouteTableId", "route_tables"),
        ("ec2", "describe_addresses", "Addresses", "PublicIp", "elastic_ips"),
        # --- COMPUTE & STORAGE ---
        ("ec2", "describe_instances", "Reservations", "InstanceId", "instances"),
        ("ec2", "describe_volumes", "Volumes", "VolumeId", "ebs_volumes"),
        ("lambda", "list_functions", "Functions", "FunctionName", "lambdas"),
        # --- DATA & SECRETS ---
        ("s3", "list_buckets", "Buckets", "Name", "s3_buckets"),
        ("dynamodb", "list_tables", "TableNames", None, "dynamodb_tables"),
        ("secretsmanager", "list_secrets", "SecretList", "Name", "secrets"),
        ("ssm", "describe_parameters", "Parameters", "Name", "ssm_parameters"),
        # --- IDENTITY ---
        ("iam", "list_users", "Users", "UserName", "iam_users")
    ]
    
    inventory = {}

    for svc_name, method, key, id_key, label in checks:
        try:
            c = client(svc_name)
            data = getattr(c, method)()
            items = []

            # Cas particulier EC2 Instances (nested)
            if method == "describe_instances":
                for res in data.get('Reservations', []):
                    for inst in res.get('Instances', []):
                        items.append(f"{inst.get(id_key)}{get_tags_string(inst)}")
            
            # Cas particulier S3 (Tags nécessitent un appel séparé)
            elif svc_name == "s3":
                for b in data.get('Buckets', []):
                    name = b.get('Name')
                    try:
                        t_data = c.get_bucket_tagging(Bucket=name)
                        tag_str = get_tags_string(t_data)
                    except: tag_str = ""
                    items.append(f"{name}{tag_str}")

            # Cas standard
            else:
                raw_list = data.get(key, [])
                for item in raw_list:
                    if id_key and isinstance(item, dict):
                        tag_str = get_tags_string(item)
                        # Ajout du nom du SG pour la lisibilité
                        suffix = f" ({item.get('GroupName')})" if method == "describe_security_groups" else ""
                        items.append(f"{item.get(id_key)}{suffix}{tag_str}")
                    else:
                        items.append(str(item))
            
            if items:
                inventory[f"{svc_name}_{label}"] = sorted(items)

            # Cas particulier IAM Roles (souvent rattachés à d'autres ressources)
            if label == "iam_users":
                roles = c.list_roles().get('Roles', [])
                role_items = [f"{r.get('RoleName')}{get_tags_string(r)}" for r in roles]
                if role_items:
                    inventory["iam_roles"] = sorted(role_items)

        except Exception:
            pass

    print(json.dumps(inventory, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    get_inventory()
