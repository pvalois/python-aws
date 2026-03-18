#!/usr/bin/env python3

from aws_local import client
from rich.table import Table, box
from rich.console import Console

iam = client("iam")
console = Console()

table = Table(box=box.SIMPLE_HEAVY)
table.add_column("Type", style="cyan")
table.add_column("Name", style="magenta")
table.add_column("Arn", style="green")
table.add_column("Policies", style="yellow")

for user in iam.list_users().get("Users", []):
    name = user['UserName']

    res = iam.get_user(UserName=name)
    arn = res['User']['Arn']

    attached = [p['PolicyName'] for p in iam.list_attached_user_policies(UserName=name).get('AttachedPolicies', [])]
    inline = iam.list_user_policies(UserName=name).get('PolicyNames', [])

    all_policies = attached + [f"{p} (inline)" for p in inline]
    policy_str = "\n".join(all_policies) if all_policies else "[grey62]No Policy[/grey62]"

    table.add_row("User", name, arn, policy_str)

for role in iam.list_roles().get("Roles", []):
    name = role['RoleName']

    res = iam.get_role(RoleName=name)
    arn = res['Role']['Arn']

    attached = [p['PolicyName'] for p in iam.list_attached_role_policies(RoleName=name).get('AttachedPolicies', [])]
    inline = iam.list_role_policies(RoleName=name).get('PolicyNames', [])

    all_policies = attached + [f"{p} (inline)" for p in inline]
    policy_str = "\n".join(all_policies) if all_policies else "[grey62]No Policy[/grey62]"

    table.add_row("Role", name, arn, policy_str)

console.print(table)
