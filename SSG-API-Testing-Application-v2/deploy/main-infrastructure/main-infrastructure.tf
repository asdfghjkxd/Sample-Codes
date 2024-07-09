# adapted from https://github.com/Harshit-cyber-bit/Terraform-Docker-AWS/blob/main/main.tf?source=post_page-----ee0a27f1f5a6--------------------------------
# and

# define ENV variables
variable "REPO_URL" {
  description = "The URL of the Docker repository to be created by ECR"
  type        = string
}

module "constants" {
  source = "../modules/constants"
}

# Specify dependencies
terraform {
  backend "s3" {
    bucket         = "ssg-tf-bucket"     # module.constants.TF_BUCKET_NAME
    key            = "main/main.tfstate" # module.constants.TF_MAIN_BUCKET_FILE_KEY
    region         = "ap-southeast-1"    # module.constants.AWS_REGION
    dynamodb_table = "ssg-tf-state-lock" # module.constants.TF_DYNAMODB_TABLE_NAME
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws",
      version = "5.17.0"
    }
  }
}

provider "aws" {
  region = module.constants.AWS_REGION
}

# Link to default VPC
resource "aws_default_vpc" "default" {

}

# reference default subnets
resource "aws_default_subnet" "subnet_1" {
  availability_zone = "ap-southeast-1a"
}

resource "aws_default_subnet" "subnet_2" {
  availability_zone = "ap-southeast-1b"
}

resource "aws_default_subnet" "subnet_3" {
  availability_zone = "ap-southeast-1c"
}

# Create roles
data "aws_iam_policy_document" "ecs_node_doc" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_node_role" {
  name_prefix        = module.constants.IAM_ROLE_NAME
  assume_role_policy = data.aws_iam_policy_document.ecs_node_doc.json
}

resource "aws_iam_role_policy_attachment" "ecs_node_role_policy" {
  role       = aws_iam_role.ecs_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "ecs_node" {
  name_prefix = module.constants.IAM_INSTANCE_PROFILE
  path        = "/ecs/instance/"
  role        = aws_iam_role.ecs_node_role.name
}

data "aws_iam_policy_document" "ecs_task_doc" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_role" {
  name_prefix        = "demo-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_doc.json
}

resource "aws_iam_role" "ecs_exec_role" {
  name_prefix        = "demo-ecs-exec-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_doc.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_role_policy" {
  role       = aws_iam_role.ecs_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create Task Definition
resource "aws_ecs_task_definition" "app" {
  family = module.constants.ECS_TASK_DEFINITION_FAMILY
  container_definitions = jsonencode([
    {
      name = module.constants.ECS_CONTAINER_NAME
      image = var.REPO_URL
      essential = true
      portMappings = [
        {
          containerPort = module.constants.CONTAINER_APPLICATION_PORT
          hostPort      = module.constants.CONTAINER_APPLICATION_PORT
        }
      ]
      memory = module.constants.ECS_TASK_MEMORY
      cpu = module.constants.ECS_TASK_CPU
    }
  ])
  requires_compatibilities = ["FARGATE"]
  network_mode = "awsvpc"
  execution_role_arn = aws_iam_role.ecs_exec_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

}

# Create ALB SG
resource "aws_security_group" "alb_sg" {
  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_alb" "alb" {
  name               = module.constants.ALB_NAME
  load_balancer_type = "application"
  subnets = [
    aws_default_subnet.subnet_1.id,
    aws_default_subnet.subnet_2.id,
    aws_default_subnet.subnet_3.id
  ]
  security_groups = [aws_security_group.alb_sg.id]
}

# Create Target Group
resource "aws_lb_target_group" "app_tg" {
  name = module.constants.TARGET_GROUP_NAME
  port = module.constants.CONTAINER_APPLICATION_PORT
  protocol = "HTTP"
  target_type = "ip"
  vpc_id = aws_default_vpc.default.id
}

# Create Listener
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_alb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# Create ECS Service
resource "aws_security_group" "service_sg" {
  ingress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [module.constants.IPV4_ALL_CIDR]
  }
}

resource "aws_ecs_service" "app" {
  name            = module.constants.ECS_SERVICE_NAME
  cluster         = module.constants.ECS_CLUSTER_NAME
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [
      aws_default_subnet.subnet_1.id,
      aws_default_subnet.subnet_2.id,
      aws_default_subnet.subnet_3.id
    ]
    security_groups = [aws_security_group.service_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = aws_ecs_task_definition.app.family
    container_port   = module.constants.CONTAINER_APPLICATION_PORT
  }
}

output "app_url" {
  value = aws_alb.alb.dns_name
}
