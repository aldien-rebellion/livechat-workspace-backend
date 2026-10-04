################################################################################
# Workshop 12 – Infrastructure as Code
# Provider: AWS (Amazon Web Services)
# Resources: EC2 Instance (Ubuntu 22.04 LTS, 1 vCPU, 1 GB RAM) + Security Group
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS Region (use 'us-east-1' for AWS Academy Learner Lab, or 'ap-southeast-1' for Singapore)"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 Instance Type (t2.micro / t3.micro = 1 vCPU, 1 GB RAM, Free Tier)"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "EC2 Key Pair name (default 'vockey' for AWS Academy, or your custom key pair name in AWS Console)"
  type        = string
  default     = "vockey"
}

variable "public_key" {
  description = "Optional: SSH public key string (e.g. file content of ~/.ssh/id_rsa.pub) to create a new Key Pair if not using existing key_name"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Key Pair (Created only if var.public_key is provided)
# ---------------------------------------------------------------------------
resource "aws_key_pair" "deployer" {
  count      = var.public_key != "" ? 1 : 0
  key_name   = "iot-deployer-key"
  public_key = var.public_key
}

# ---------------------------------------------------------------------------
# Default VPC & Security Group
# ---------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "iot_sg" {
  name        = "iot-api-sg"
  description = "Security Group for IoT API Server (Ports 22, 80, 443, 8000)"
  vpc_id      = data.aws_vpc.default.id

  # Port 22: SSH Access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 80: HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 443: HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 8000: IoT API
  ingress {
    description = "IoT API (FastAPI)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound: Allow all traffic
  egress {
    description      = "Allow all outbound traffic"
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "iot-api-sg"
    Environment = "Workshop12"
  }
}

# ---------------------------------------------------------------------------
# AMI: Ubuntu 22.04 LTS (Jammy)
# ---------------------------------------------------------------------------
data "aws_ami" "ubuntu_22" {
  most_recent = true
  owners      = ["099720109477"] # Canonical official owner ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------------------------------------------------------------------------
# EC2 Instance
# ---------------------------------------------------------------------------
resource "aws_instance" "iot_server" {
  ami           = data.aws_ami.ubuntu_22.id
  instance_type = var.instance_type

  key_name = var.public_key != "" ? aws_key_pair.deployer[0].key_name : (var.key_name != "" ? var.key_name : null)

  vpc_security_group_ids = [aws_security_group.iot_sg.id]

  # User data: auto-install Docker & Docker Compose on first boot
  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Docker Engine
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add ubuntu user to docker group
    usermod -aG docker ubuntu

    # Create app directory
    mkdir -p /home/ubuntu/app
    chown -R ubuntu:ubuntu /home/ubuntu/app
  EOF

  tags = {
    Name        = "iot-api-server"
    Environment = "Workshop12"
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.iot_server.public_ip
}

output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.iot_server.id
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh ubuntu@${aws_instance.iot_server.public_ip}"
}

################################################################################
# ── DIGITALOCEAN ALTERNATIVE ─────────────────────────────────────────────────
# Uncomment the block below if you wish to switch back to DigitalOcean.
################################################################################

# terraform {
#   required_providers {
#     digitalocean = {
#       source  = "digitalocean/digitalocean"
#       version = "~> 2.0"
#     }
#   }
# }
# provider "digitalocean" { token = var.do_token }
# resource "digitalocean_droplet" "iot_server" {
#   name   = "iot-api-server"
#   region = "sgp1"
#   size   = "s-1vcpu-1gb"
#   image  = "ubuntu-22-04-x64"
#   ssh_keys = [var.ssh_key_fingerprint]
# }
