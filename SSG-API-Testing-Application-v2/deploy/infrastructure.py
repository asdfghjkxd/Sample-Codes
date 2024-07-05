"""
IaC template for creating base cloud environment

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

# set up VPC
ec2 = boto3.client("ec2", config=config)

vpc = ec2.create_vpc(
    CidrBlock="172.16.0.0/16"
)

vpc.wait_until_available()

# enable public DNS hostname for SSH
ec2.modify_vpc_attribute(
    VpcId=vpc.id, EnableDnsSupport={"Value": True}
)
ec2.modify_vpc_attribute(
    VpcId=vpc.id, EnableDnsHostnames={"Value": True}
)

# create internet gateway
ig = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=ig.id)

# create a routing table
rt = vpc.create_route_table()
route = rt.create_route(
    DestinationCidrBlock="0.0.0.0/0", GatewayId=ig.id
)

# create subnets and associate it with the routing table
subnet1 = ec2.create_subnet(
    AvailabilityZone="ap-southeast-1a",
    CidrBlock="172.16.32.0/20",
    VpcId=vpc.id
)

subnet2 = ec2.create_subnet(
    AvailabilityZone="ap-southeast-1b",
    CidrBlock="172.16.16.0/20",
    VpcId=vpc.id
)

rt.associate_with_subnet(SubnetId=subnet1.id)
rt.associate_with_subnet(SubnetId=subnet2.id)

# form the required Security Groups, Ingress Rules and Launch Templates
sg = ec2.create_security_group(
    Description="Security group for SSG-WSG Sample Application",
    GroupName=SG_GROUP_NAME,
    VpcId=vpc.id  # CHANGE THIS TO YOUR VPC ID IN THE REGION
)

sg_ingress = ec2.authorize_security_group_ingress(
    CidrIp="0.0.0.0/32",
    FromPort=80,
    GroupId=sg["GroupId"],
    GroupName=SG_GROUP_NAME,
    IpPermissions=[
        {
            "FromPort": 80,
            "ToPort": 8502,  # THIS MUST BE CHANGED TO THE PORT NUMBER THAT THE APPLICATED IS SERVED ON
            "IpProtocol": "tcp",
            "IpRanges": [
                {
                    "CidrIp": "0.0.0.0/32",
                    "Description": "Allow HTTP traffic from anywhere"
                }
            ],
            "Ipv6Ranges": [],
            "PrefixListIds": [],
            "UserIdGroupPairs": []
        },
        {
            "FromPort": 433,
            "ToPort": 8502,  # THIS MUST BE CHANGED TO THE PORT NUMBER THAT THE APPLICATED IS SERVED ON
            "IpProtocol": "tcp",
            "IpRanges": [
                {
                    "CidrIp": "0.0.0.0/32",
                    "Description": "Allow HTTPS traffic from anywhere"
                }
            ],
            "Ipv6Ranges": [],
            "PrefixListIds": [],
            "UserIdGroupPairs": []
        }
    ]
)

launch_template = ec2.create_launch_template(
    LaunchTemplateName="ssg-wsg-launch-template",
    LaunchTemplateData={
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {
                    "Encrypted": False,
                    "Iops": 3000,
                    "DeleteOnTermination": True,
                    "VolumeSize": 15,
                    "VolumeType": "gp3",
                    "Throughput": 300,
                }
            }
        ],
        "ImageId": "ami-06d753822bd94c64e",  # CHANGE THIS TO YOUR AMI ID,
        "InstanceType": "t2.micro",
        "CreditSpecification": {
            "CpuCredits": "standard"
        },
        "SecurityGroupIds": [
            sg["GroupId"]
        ]
    }
)


# create ASG client
asg = boto3.resource("autoscaling", config=config)

# create launch template
asg_group = asg.create_auto_scaling_group(
    AutoScalingGroupName="ssg-wsg-asg",
    LaunchTemplate={
        "LaunchTemplateId": launch_template["LaunchTemplateId"],
        "Version": "$Latest"
    },
    MaxSize=1,
    MinSize=1,
    DesiredCapacity=1,
    AvailabilityZones=[
        "ap-southeast-1a",
        "ap-southeast-1b"
    ]
)

# create ecr repo
ecr = boto3.client("ecr", config=config)

repo = ecr.create_repository(
    repositoryName=os.getenv("ECR_REPO_NAME"),
    catalogData={
        "description": "SSG-WSG Sample Application",
        "architectures": [
            "X86_64"
        ],
        "operatingSystems": [
            "LINUX"
        ]
    }
)

# taken from
# https://stackoverflow.com/questions/70123328/how-to-set-environment-variables-in-github-actions-using-python
env_file = os.getenv("GITHUB_ENV")

with open(env_file, "a") as f:
    f.write(f"VPC_ID={vpc.id}\n")
    f.write(f"ASG_ARN={asg_group["AutoScalingGroups"][0]["AutoScalingGroupARN"]}\n")
    f.write(f"SUBNET1_ID={subnet1.id}\n")
    f.write(f"SUBNET2_ID={subnet2.id}\n")
    f.write(f"SECURITY_GROUP_ID={sg['GroupId']}\n")
    f.write(f"LAUNCH_TEMPLATE_ID={launch_template['LaunchTemplate']['LaunchTemplateId']}\n")
    f.write(f"ECR_REPO_URI={repo['repository']['repositoryUri']}\n")
    f.write(f"ECR_REGISTRY={repo['repository']['registryId']}\n")
    f.write(f"ECR_REPO_NAME={repo['repository']['repositoryName']}\n")
