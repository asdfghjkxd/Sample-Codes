"""
IaC template for setting up ECS stack

Inspired from https://aws.plainenglish.io/creating-vpc-using-boto3-terraform-cloudformation-and-both-af741a8afb3c
"""

import os
import boto3

from botocore.config import Config
from app.core.system.logger import Logger

# create logger
LOGGER = Logger("cloudformation")

# define parameters to be used in the stack
SG_GROUP_NAME = "ssg-wsg"

config = Config(
    region_name="ap-southeast-1"  # CHANGE THIS TO YOUR REGION OF CHOICE
)

# create ECS client
ecs = boto3.resource("ecs", config=config)

# create ECS cluster
capacity_provider = ecs.create_capacity_provider(
    name="ssg-capacity-provider",
    autoScalingGroupProvider={
        "autoScalingGroupArn": os.getenv("ASG_ARN"),
        "managedScaling": {
            "status": "ENABLED",
            "targetCapacity": 1,
            "minimumScalingStepSize": 1,
            "maximumScalingStepSize": 1
        },
    }
)

create_cluster = ecs.create_cluster(
    clusterName=os.getenv("ECS_CLUSTER_NAME"),
    capacityProviders=[
        capacity_provider["capacityProvider"]["capacityProviderArn"]
    ]
)

task_definition = ecs.register_task_definition(
    family="app",
    networkMode="bridge",
    containerDefinitions=[
        {
            "name": "app",
            "image": os.getenv("ECS_IMAGE"),
            "portMappings": [
                {
                    "containerPort": 8502,
                    "hostPort": 80,
                    "protocol": "tcp",
                    "appProtocol": "http"
                }
            ],
            "essential": True,
            "disableNetworking": False,
            "privileged": True,
            "readonlyRootFilesystem": False,
            "interactive": True,
            "pseudoTerminal": True
        }
    ],
    requiresCompatibilities=[
        "EC2"
    ],
    healthCheck={
        "command": ["CMD-SHELL", "curl -f http://localhost:8502/ || exit 1"],
        "interval": 60,
        "timeout": 15,
        "retries": 3
    },
    runtimePlatform={
        "cpuArchitecture": "X86_64",
        "operatingSystemFamily": "LINUX"
    }
)

create_service = ecs.create_service(
    cluster=create_cluster["cluster"]["clusterArn"],
    serviceName=os.getenv("ECS_SERVICE_NAME"),
    taskDefinition=task_definition["taskDefinition"]["taskDefinitionArn"],
    desiredCount=1,
    launchType="EC2",
    networkConfiguration={
        "awsvpcConfiguration": {
            "subnets": [
                os.getenv("SUBNET1_ID"),  # SPECIFY YOUR SUBNET IDs HERE
                os.getenv("SUBNET2_ID"),  # SPECIFY YOUR SUBNET IDs HERE
            ],
            "securityGroups": [
                os.getenv("SECURITY_GROUP_ID")
            ],
            "assignPublicIp": "ENABLED"
        }
    },
    schedulingStrategy="REPLICA",
    deploymentController={
        "type": "ECS"
    },
)


# taken from
# https://stackoverflow.com/questions/70123328/how-to-set-environment-variables-in-github-actions-using-python
env_file = os.getenv("GITHUB_ENV")

with open(env_file, "a") as f:
    f.write(f"CAPACITY_PROVIDER_ARN={capacity_provider['capacityProvider']['name']}\n")
    f.write(f"TASK_DEFINITION_ARN={task_definition['taskDefinition']['taskDefinitionArn']}\n")
    f.write(f"CLUSTER_ARN={create_cluster['cluster']['clusterArn']}\n")
    f.write(f"SERVICE_ARN={create_service['service']['serviceArn']}\n")
