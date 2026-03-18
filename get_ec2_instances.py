#!/usr/bin/env python3

import boto3
from botocore.client import Config
from aws_local import client
from rich.table import Table,box
from rich.console import Console

def get_instances():
    """
    Retourne la liste des instances EC2 visibles sur l'endpoint configuré.
    """
    ec2 = client("ec2")

    try:
        response = ec2.describe_instances()
    except Exception as e:
        print(f"Erreur describe_instances : {e}")
        return []

    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):

            tags = inst.get("Tags", [])

            yield({
                "InstanceId": inst.get("InstanceId"),
                "Type": inst.get("InstanceType"),
                "State": inst.get("State", {}).get("Name"),
                "PrivateIP": inst.get("PrivateIpAddress"),
                "PublicIP": inst.get("PublicIpAddress"),
                "LaunchTime": inst.get("LaunchTime"),
                "Tags": tags,
                })

if __name__ == "__main__":

    table=Table(box=box.SIMPLE_HEAVY)

    table.add_column("Instance ID")
    table.add_column("Type")
    table.add_column("State")
    table.add_column("Private IP")
    table.add_column("Public IP")
    table.add_column("Launch Time")
    table.add_column("Tags")

    for inst in get_instances():
        state = inst["State"]
    
        color = "green" if state == "running" else "red" if state == "stopped" else "yellow"
        launch_str = inst["LaunchTime"].strftime("%Y-%m-%d %H:%M") if inst["LaunchTime"] else "N/A"

        table.add_row(
            inst["InstanceId"],
            inst["Type"],
            f"[{color}]{state}[/{color}]",
            str(inst["PrivateIP"]),
            str(inst["PublicIP"]),
            launch_str,
            "\n".join([f"{tag['Key']} -> {tag['Value']}" for tag in inst.get("Tags", [])])
        )

    console=Console()
    console.print(table)
