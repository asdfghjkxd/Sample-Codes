# define ENV variables
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

# Create ECR repository
resource "aws_ecr_repository" "app" {
  name                 = module.constants.ECR_REPO_NAME
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

locals {
  repo_url = aws_ecr_repository.app.repository_url
}

resource "null_resource" "image" {
  triggers = {
    hash = md5(join("-", [for x in fileset("", "./{*.py, Dockerfile}") : filemd5(x)]))
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password | docker login --username AWS --password-stdin ${local.repo_url}
      docker build --platform linux/amd64 -t ${local.repo_url}:latest ../../app/
      docker push ${local.repo_url}:latest
    EOF
  }
}

data "aws_ecr_image" "latest" {
  repository_name = aws_ecr_repository.app.name
  image_tag       = "latest"
  depends_on      = [null_resource.image]
}

# Create cluster
resource "aws_ecs_cluster" "cluster" {
  name = module.constants.ECS_CLUSTER_NAME
}

# Create IAM policy document for ecsTaskExecutionRole
data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["ecs-tasks.amazonaws.com"]
      type        = "Service"
    }
  }
}

# Create IAM role for ECS task execution
resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = module.constants.ECS_EXECUTION_ROLE_NAME
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
}

# Attach IAM role to ecsTaskExecutionRole
resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRoleAttachment" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create Task Definition
resource "aws_ecs_task_definition" "task" {
  family = module.constants.ECS_TASK_DEFINITION_FAMILY
  container_definitions = jsonencode([
    {
      name      = module.constants.ECS_CONTAINER_NAME
      image     = aws_ecr_repository.app.repository_url
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = module.constants.CONTAINER_APPLICATION_PORT
          hostPort      = module.constants.CONTAINER_APPLICATION_PORT
        }
      ]
    }
  ])
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  memory                   = 512
  cpu                      = 256
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn
}

# Create Reference to default VPC
resource "aws_default_vpc" "default_vpc" {

}

# Create Reference to Subnets
resource "aws_default_subnet" "default_subnet_a" {
  availability_zone = "ap-southeast-1a"
}

resource "aws_default_subnet" "default_subnet_b" {
  availability_zone = "ap-southeast-1b"
}

resource "aws_default_subnet" "default_subnet_c" {
  availability_zone = "ap-southeast-1c"
}

# Create Load Balancer
resource "aws_alb" "lb" {
  name               = module.constants.ALB_NAME
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ssg_lb_sg.id]
  subnets = [
    aws_default_subnet.default_subnet_a.id,
    aws_default_subnet.default_subnet_b.id,
    aws_default_subnet.default_subnet_c.id
  ]
}

# Create Security Group
resource "aws_security_group" "ssg_lb_sg" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create TG
resource "aws_lb_target_group" "aws_tg" {
  name        = module.constants.TARGET_GROUP_NAME
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_default_vpc.default_vpc.id

  health_check {
    matcher = "200,301,302"
    path    = "/"
  }
}

# Create Listener for TG
resource "aws_lb_listener" "aws_listener" {
  load_balancer_arn = aws_alb.lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.aws_tg.arn
  }
}

# Create Service
resource "aws_ecs_service" "service" {
  name            = module.constants.ECS_SERVICE_NAME
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.task.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  load_balancer {
    target_group_arn = aws_lb_target_group.aws_tg.arn
    container_name   = module.constants.ECS_CONTAINER_NAME
    container_port   = 80
  }

  network_configuration {
    subnets = [
      aws_default_subnet.default_subnet_a.id,
      aws_default_subnet.default_subnet_b.id,
      aws_default_subnet.default_subnet_c.id
    ]
    assign_public_ip = true
    security_groups  = [aws_security_group.ssg_service_sg.id]
  }
}

# Create SG for Service
resource "aws_security_group" "ssg_service_sg" {
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.ssg_lb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Output DNS Name
output "lb_dns" {
  value = aws_alb.lb.dns_name
}
