#!/usr/bin/env python3
import boto3
import argparse
from datetime import datetime, timedelta, timezone

def get_cost(resource_id, start, end, ce_client):
    try:
        resp = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start, 'End': end},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={'Dimensions': {'Key': 'RESOURCE_ID', 'Values': [resource_id]}}
        )
        amount = resp['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        return float(amount)
    except Exception:
        return None

def get_cost_service(service_name, start, end, ce_client):
    try:
        resp = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start, 'End': end},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            Filter={'Dimensions': {'Key': 'SERVICE', 'Values': [service_name]}}
        )
        amount = resp['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        return float(amount)
    except Exception:
        return None

def list_ec2(ec2): return [i.id for i in ec2.instances.all()]
def list_ebs(ec2): return [v.id for v in ec2.volumes.all()]
def list_s3(s3): return [b.name for b in s3.buckets.all()]
def list_elb(elb): return [lb['LoadBalancerName'] for lb in elb.describe_load_balancers()['LoadBalancerDescriptions']]
def list_rds(rds): return [db['DBInstanceIdentifier'] for db in rds.describe_db_instances()['DBInstances']]
def list_lambda(lambda_client): return [fn['FunctionName'] for fn in lambda_client.list_functions()['Functions']]
def list_subnets(ec2): return [s.id for s in ec2.subnets.all()]
def list_dynamodb(ddb): return [t['TableName'] for t in ddb.list_tables()['TableNames']]
def list_redshift(rs): return [c['ClusterIdentifier'] for c in rs.describe_clusters()['Clusters']]
def list_sqs(sqs): return [q.split('/')[-1] for q in sqs.list_queues().get('QueueUrls', [])]
def list_sns(sns): return [t['TopicArn'].split(':')[-1] for t in sns.list_topics().get('Topics', [])]

def print_output(resources, prometheus=False):
    if prometheus:
        for rtype, rid, cost in resources:
            value = cost if cost is not None else 0
            metric_name = "aws_cost"
            print(f'{metric_name}{{resource="{rid}",type="{rtype}"}} {value}')
    else:
        print(f"{'Type':<15} {'ResourceId':<40} {'Cost($)':>10}")
        print("-"*70)
        for rtype, rid, cost in resources:
            cost_str = f"{cost:.2f}" if cost is not None else "N/A"
            print(f"{rtype:<15} {rid:<40} {cost_str:>10}")

def main(profile, period_days, prometheus=False):
    session = boto3.Session(profile_name=profile)
    ce = session.client('ce')
    ec2 = session.resource('ec2')
    s3 = session.resource('s3')
    elb = session.client('elb')
    rds = session.client('rds')
    lambda_client = session.client('lambda')
    ddb = session.client('dynamodb')
    rs = session.client('redshift')
    sqs = session.client('sqs')
    sns = session.client('sns')

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=period_days)
    start_str, end_str = start.isoformat(), end.isoformat()

    resources = []

    for i in list_ec2(ec2): resources.append(('EC2', i, get_cost(i, start_str, end_str, ce)))
    for v in list_ebs(ec2): resources.append(('EBS', v, get_cost(v, start_str, end_str, ce)))
    for b in list_s3(s3): resources.append(('S3', b, get_cost(b, start_str, end_str, ce)))
    for lb in list_elb(elb): resources.append(('ELB', lb, get_cost(lb, start_str, end_str, ce)))
    for db in list_rds(rds): resources.append(('RDS', db, get_cost(db, start_str, end_str, ce)))
    for fn in list_lambda(lambda_client): resources.append(('Lambda', fn, get_cost(fn, start_str, end_str, ce)))
    for sn in list_subnets(ec2): resources.append(('Subnet', sn, None))
    for t in list_dynamodb(ddb): resources.append(('DynamoDB', t, get_cost(t, start_str, end_str, ce)))
    for c in list_redshift(rs): resources.append(('Redshift', c, get_cost(c, start_str, end_str, ce)))
    for q in list_sqs(sqs): resources.append(('SQS', q, get_cost(q, start_str, end_str, ce)))
    for t in list_sns(sns): resources.append(('SNS', t, get_cost(t, start_str, end_str, ce)))

    # NAT Gateway / CloudFront coûts globaux
    nat_cost = get_cost_service('NAT Gateway', start_str, end_str, ce)
    resources.append(('NAT Gateway', 'All', nat_cost))
    cf_cost = get_cost_service('Amazon CloudFront', start_str, end_str, ce)
    resources.append(('CloudFront', 'All', cf_cost))

    print_output(resources, prometheus)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lister toutes les ressources AWS et leur coût")
    parser.add_argument('-P', '--profile', default='default', help="Profil AWS à utiliser")
    parser.add_argument('-d', '--days', type=int, default=30, help="Nombre de jours pour le calcul du coût")
    parser.add_argument('-p', '--prometheus', action='store_true', help="Sortie au format Prometheus")
    args = parser.parse_args()

    try:
        main(args.profile, args.days, args.prometheus)
    except Exception as e:
        print(f"Erreur: {e}")
        exit(1)
