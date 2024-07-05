"""
IaC template for setting up ECS stack

Inspired from https://aws.plainenglish.io/creating-vpc-using-boto3-terraform-cloudformation-and-both-af741a8afb3c
"""

import os
import boto3
import logging

from botocore.config import Config

# define parameters to be used in the stack
SG_GROUP_NAME = "ssg-wsg"
LOGGER = logging.getLogger("infra")
LOGGER.setLevel(logging.INFO)
STREAM_HANDLER = logging.StreamHandler()
STREAM_HANDLER.setLevel(logging.INFO)
LOGGER.addHandler(STREAM_HANDLER)

config = Config(
    region_name="ap-southeast-1"  # CHANGE THIS TO YOUR REGION OF CHOICE
)

# create ECS client
ecs = boto3.client("ecs", config=config)

# create task definition
LOGGER.info("Creating task definition...")
task_definition = ecs.register_task_definition(
    family="app",
    networkMode="awsvpc",
    containerDefinitions=[
        {
            "memory": 512,
            "cpu": 512,
            "name": os.getenv("ECS_CONTAINER_NAME"),
            "image": os.getenv("ECS_IMAGE"),
            "portMappings": [
                {
                    "containerPort": 8502,
                    "hostPort": 80,
                    "protocol": "tcp",
                    "appProtocol": "http"
                }
            ],
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8502/ || exit 1"],
                "interval": 60,
                "timeout": 15,
                "retries": 3
            },
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
    runtimePlatform={
        "cpuArchitecture": "X86_64",
        "operatingSystemFamily": "LINUX"
    }
)
LOGGER.info(f"Task definition created successfully! Task Definition ARN: {task_definition['taskDefinition']['taskDefinitionArn']}")

create_service = ecs.create_service(
    cluster=os.getenv("ECS_CLUSTER_ARN"),
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
    f.write(f"TASK_DEFINITION_ARN={task_definition['taskDefinition']['taskDefinitionArn']}\n")
    f.write(f"SERVICE_ARN={create_service['service']['serviceArn']}\n")
