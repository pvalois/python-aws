#!/usr/bin/env python3

import json
from aws_local import client

services = {
    "ec2": lambda c: c.describe_instances(),
    "ecs": lambda c: c.list_clusters(),
    "s3": lambda c: c.list_buckets(),
    "lambda": lambda c: c.list_functions(),
    "sqs": lambda c: c.list_queues(),
    "sns": lambda c: c.list_topics(),
    "dynamodb": lambda c: c.list_tables(),
    "apigateway": lambda c: c.get_rest_apis(),
}

snapshot = {}

for name, fn in services.items():
    try:
        c = client(name)
        snapshot[name] = fn(c)
    except Exception as e:
        snapshot[name] = {
            "error": str(e),
        }

print(json.dumps(snapshot, indent=2, default=str))
