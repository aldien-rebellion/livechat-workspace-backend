################################################################################
# Workshop 12 – Infrastructure as Code
# Provider: DigitalOcean  (switch to AWS section below if preferred)
# Resources: Droplet (Ubuntu 22.04, 1 vCPU, 1 GB RAM) + Firewall
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
variable "do_token" {
  description = "DigitalOcean Personal Access Token"
  type        = string
  sensitive   = true
}

variable "ssh_key_fingerprint" {
  description = "Fingerprint of the SSH public key already added to your DigitalOcean account"
  type        = string
}

variable "region" {
  description = "DigitalOcean region slug (e.g. sgp1, nyc3)"
  type        = string
  default     = "sgp1" # Singapore – closest to Thailand
}

variable "droplet_name" {
  description = "Name for the Droplet"
  type        = string
  default     = "iot-api-server"
}

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
provider "digitalocean" {
  token = var.do_token
}

# ---------------------------------------------------------------------------
# Droplet  (Ubuntu 22.04, s-1vcpu-1gb = 1 vCPU / 1 GB RAM)
# ---------------------------------------------------------------------------
resource "digitalocean_droplet" "iot_server" {
  name   = var.droplet_name
  region = var.region
  size   = "s-1vcpu-1gb"   # 1 vCPU, 1 GB RAM
  image  = "ubuntu-22-04-x64"

  ssh_keys  = [var.ssh_key_fingerprint]
  monitoring = true

  tags = ["iot-api", "workshop12"]

  # Cloud-init: install Docker & Docker Compose on first boot
  user_data = <<-EOF
    #!/bin/bash
    set -e
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release

    # Docker Engine
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) \
      signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io \
                       docker-buildx-plugin docker-compose-plugin

    # Add ubuntu user to docker group
    usermod -aG docker ubuntu

    # Create app directory
    mkdir -p /home/ubuntu/app
    chown ubuntu:ubuntu /home/ubuntu/app
  EOF
}

# ---------------------------------------------------------------------------
# Firewall
# ---------------------------------------------------------------------------
resource "digitalocean_firewall" "iot_firewall" {
  name = "${var.droplet_name}-fw"

  droplet_ids = [digitalocean_droplet.iot_server.id]

  # ── Inbound ──────────────────────────────────────────────────────────────
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "8000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # ── Outbound (allow all) ──────────────────────────────────────────────────
  outbound_rule {
    protocol              = "tcp"
    port_range            = "all"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "all"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "public_ip" {
  description = "Public IP address of the IoT API server"
  value       = digitalocean_droplet.iot_server.ipv4_address
}

output "droplet_id" {
  description = "Droplet ID"
  value       = digitalocean_droplet.iot_server.id
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh ubuntu@${digitalocean_droplet.iot_server.ipv4_address}"
}

################################################################################
# ── AWS ALTERNATIVE ──────────────────────────────────────────────────────────
# Uncomment the block below and comment out the DigitalOcean section above
# if you prefer AWS EC2 (t3.micro = 2 vCPU / 1 GB RAM, free-tier eligible).
################################################################################

# terraform {
#   required_providers {
#     aws = {
#       source  = "hashicorp/aws"
#       version = "~> 5.0"
#     }
#   }
# }
#
# variable "aws_region" { default = "ap-southeast-1" }  # Singapore
# variable "key_name"   { description = "EC2 Key Pair name" }
#
# provider "aws" { region = var.aws_region }
#
# resource "aws_security_group" "iot_sg" {
#   name        = "iot-api-sg"
#   description = "Allow SSH, HTTP, HTTPS, IoT API"
#
#   ingress { from_port=22   to_port=22   protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
#   ingress { from_port=80   to_port=80   protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
#   ingress { from_port=443  to_port=443  protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
#   ingress { from_port=8000 to_port=8000 protocol="tcp" cidr_blocks=["0.0.0.0/0"] }
#   egress  { from_port=0    to_port=0    protocol="-1"  cidr_blocks=["0.0.0.0/0"] }
# }
#
# data "aws_ami" "ubuntu_22" {
#   most_recent = true
#   owners      = ["099720109477"]  # Canonical
#   filter { name="name"                values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"] }
#   filter { name="virtualization-type" values=["hvm"] }
# }
#
# resource "aws_instance" "iot_server" {
#   ami                    = data.aws_ami.ubuntu_22.id
#   instance_type          = "t3.micro"
#   key_name               = var.key_name
#   vpc_security_group_ids = [aws_security_group.iot_sg.id]
#
#   user_data = <<-EOF
#     #!/bin/bash
#     apt-get update -y
#     apt-get install -y docker.io docker-compose-plugin
#     usermod -aG docker ubuntu
#     mkdir -p /home/ubuntu/app && chown ubuntu:ubuntu /home/ubuntu/app
#   EOF
#
#   tags = { Name = "iot-api-server" }
# }
#
# output "public_ip" { value = aws_instance.iot_server.public_ip }
