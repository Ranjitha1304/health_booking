terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Get latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"] # Ensure x86 architecture
  }

  owners = ["099720109477"] # Canonical's AWS account ID
}

# Get SSH public key from Windows path
locals {
  ssh_public_key = file("C:/Users/thanu/.ssh/id_rsa.pub")
}

# Create EC2 Key Pair
resource "aws_key_pair" "healthcare_key" {
  key_name   = "healthcare-key"
  public_key = local.ssh_public_key
}

# Create Security Group
resource "aws_security_group" "ec2_sg" {
  name        = "healthcare-ec2-sg"
  description = "Security group for healthcare EC2 instance"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Django application"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create EC2 Instance
resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro" # CHANGED TO t3.micro (Free tier eligible)
  key_name               = aws_key_pair.healthcare_key.key_name
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install docker.io docker-compose -y
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -aG docker ubuntu
              EOF

  tags = {
    Name = "healthcare-web-server"
  }
}

# Output the important information
output "ec2_public_ip" {
  value = aws_instance.web.public_ip
}

output "ec2_ssh_command" {
  value = "ssh -i C:/Users/thanu/.ssh/id_rsa ubuntu@${aws_instance.web.public_ip}"
}

output "web_url" {
  value = "http://${aws_instance.web.public_ip}:8000"
}

output "ami_id_used" {
  value = data.aws_ami.ubuntu.id
}