#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import argparse
import sys
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE_HEAVY

def get_all_resource_costs(start, end, ce_client):
    costs_map = {}
    try:
        paginator = ce_client.get_paginator('get_cost_and_usage_with_resources')
        param = {
            'TimePeriod': {'Start': start, 'End': end},
            'Granularity': 'MONTHLY',
            'Metrics': ['UnblendedCost'],
            'GroupBy': [{'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}]
        }
        for page in paginator.paginate(**param):
            for result in page['ResultsByTime']:
                for group in result['Groups']:
                    rid = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    costs_map[rid] = costs_map.get(rid, 0.0) + amount
    except:
        pass
    return costs_map

def get_all_service_costs(start, end, ce_client):
    service_map = {}
    try:
        resp = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start, 'End': end},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        for result in resp['ResultsByTime']:
            for group in result['Groups']:
                svc = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                service_map[svc] = amount
    except:
        pass
    return service_map

def list_ec2(s): return [i.id for i in s.resource('ec2').instances.all()]
def list_ebs(s): return [v.id for v in s.resource('ec2').volumes.all()]
def list_s3(s): return [b.name for b in s.resource('s3').buckets.all()]
def list_elb(s): return [lb['LoadBalancerName'] for lb in s.client('elb').describe_load_balancers()['LoadBalancerDescriptions']]
def list_rds(s): return [db['DBInstanceIdentifier'] for db in s.client('rds').describe_db_instances()['DBInstances']]
def list_lambda(s): return [fn['FunctionName'] for fn in s.client('lambda').list_functions()['Functions']]
def list_subnets(s): return [sn.id for sn in s.resource('ec2').subnets.all()]
def list_dynamodb(s): return s.client('dynamodb').list_tables()['TableNames']
def list_redshift(s): return [c['ClusterIdentifier'] for c in s.client('redshift').describe_clusters()['Clusters']]
def list_sqs(s): return [q.split('/')[-1] for q in s.client('sqs').list_queues().get('QueueUrls', [])]
def list_sns(s): return [t['TopicArn'].split(':')[-1] for t in s.client('sns').list_topics().get('Topics', [])]

def print_output(resources, prometheus=False):
    if prometheus:
        for rtype, rid, cost in resources:
            val = cost if cost is not None else 0.0
            print(f'aws_cost{{resource="{rid}",type="{rtype}"}} {val:.4f}')
    else:
        console = Console()
        table = Table(box=SIMPLE_HEAVY, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Resource ID", style="white")
        table.add_column("Cost ($)", justify="right", style="green")

        for rtype, rid, cost in resources:
            c_str = f"{cost:.2f}" if cost is not None else "0.00"
            table.add_row(rtype, rid, c_str)
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--profile', default='default')
    parser.add_argument('-d', '--days', type=int, default=30)
    parser.add_argument('-p', '--prometheus', action='store_true')
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    ce = session.client('ce')

    end_dt = datetime.now(timezone.utc).date()
    start_dt = end_dt - timedelta(days=args.days)
    s_str, e_str = start_dt.isoformat(), end_dt.isoformat()

    res_costs = get_all_resource_costs(s_str, e_str, ce)
    svc_costs = get_all_service_costs(s_str, e_str, ce)

    tasks = [
        ('EC2', list_ec2, False),
        ('EBS', list_ebs, False),
        ('S3', list_s3, False),
        ('ELB', list_elb, False),
        ('RDS', list_rds, False),
        ('Lambda', list_lambda, False),
        ('Subnet', list_subnets, False),
        ('DynamoDB', list_dynamodb, False),
        ('Redshift', list_redshift, False),
        ('SQS', list_sqs, False),
        ('SNS', list_sns, False),
        ('NAT Gateway', 'NAT Gateway', True),
        ('CloudFront', 'Amazon CloudFront', True),
    ]

    inventory = []

    for label, action, is_global in tasks:
        try:
            if is_global:
                cost = svc_costs.get(action, 0.0)
                inventory.append((label, 'All Resources', cost))
            else:
                items = action(session)
                for item in items:
                    cost = res_costs.get(item, 0.0)
                    inventory.append((label, item, cost))
        except:
            pass

    print_output(inventory, args.prometheus)

if __name__ == "__main__":
    main()
