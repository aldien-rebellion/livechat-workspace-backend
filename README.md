# IoT Monitoring System — Workshop 12: Cloud Deployment Guide

> **Stack:** FastAPI · Uvicorn · Docker · Terraform · GitHub Actions · DigitalOcean (or AWS)

---

## 📁 Project Structure (Workshop 12 additions)

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Workshop 11 – Lint, Test, Docker build verify
│       └── cd.yml                  # Workshop 12 – Build→Push→Deploy pipeline
├── app/
│   ├── __init__.py
│   └── main.py                     # +GET /health endpoint
├── infrastructure/
│   └── main.tf                     # Terraform – provisions cloud server
├── tests/
│   └── test_health.py              # +test_health_endpoint()
├── docker-compose.yml              # Local dev stack
├── docker-compose.prod.yml         # Production stack (runs on cloud server)
├── Dockerfile
└── requirements.txt
```

---

## 🚀 Step-by-Step Deployment Guide

### Step 1 — Install Terraform CLI

```bash
# macOS (Homebrew)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor \
  | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install terraform

# Windows (winget)
winget install HashiCorp.Terraform

# Verify
terraform -v
```

### Step 2 — Provision the Cloud Server with Terraform (AWS)

Make sure you have your AWS credentials set up locally:
- **If using AWS Academy (Learner Lab):** Click **AWS Details** in the Learner Lab, copy the **AWS CLI credentials** block, and paste it into `~/.aws/credentials`. (Region is `us-east-1`, Key Pair name is usually `vockey`).
- **If using Personal AWS Account:** Run `aws configure` and input your `AWS Access Key ID`, `Secret Access Key`, and default region (e.g. `us-east-1` or `ap-southeast-1`).

```bash
cd infrastructure/

# 1. Initialise Terraform and download AWS provider
terraform init

# 2. Preview what will be created
# If using AWS Academy:
terraform plan -var="aws_region=us-east-1" -var="key_name=vockey"

# Or if you have a custom key pair name in AWS Console:
# terraform plan -var="aws_region=ap-southeast-1" -var="key_name=your-key-name"

# 3. Apply – create the EC2 Instance + Security Group
terraform apply -var="aws_region=us-east-1" -var="key_name=vockey"

# Note the PUBLIC IP printed in the outputs:
#   public_ip    = "54.xxx.xxx.xxx"
#   ssh_command  = "ssh ubuntu@54.xxx.xxx.xxx"
```

> [!TIP]
> You can also create a `terraform.tfvars` file inside `infrastructure/` to avoid typing variables:
> ```hcl
> aws_region = "us-east-1"
> key_name   = "vockey"
> ```

To destroy the server when finished:
```bash
terraform destroy -var="aws_region=us-east-1" -var="key_name=vockey"
```

---

### Step 3 — Set Up SSH Key Pair

> [!IMPORTANT]
> Generate an SSH key pair **locally**. The private key goes into GitHub Secrets; the public key goes on the server.

```bash
# Generate a dedicated deploy key (no passphrase for automated CI/CD)
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/id_rsa_deploy -N ""

# View your public key (add this to DigitalOcean → Settings → Security → SSH Keys)
cat ~/.ssh/id_rsa_deploy.pub

# View your private key (copy this into GitHub Secret SSH_PRIVATE_KEY)
cat ~/.ssh/id_rsa_deploy
```

If your server is already running and you need to add the key manually:

```bash
# SSH into the server using the key that was provisioned by Terraform
ssh ubuntu@<PUBLIC_IP>

# On the server – append the new deploy public key
echo "ssh-rsa AAAA...your_public_key..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

### Step 4 — Install Docker on the Server (Manual / If cloud-init didn't run)

> [!NOTE]
> The `user_data` script in `infrastructure/main.tf` installs Docker automatically on first boot.
> Run these steps only if you provisioned the server manually.

```bash
# SSH into the server
ssh ubuntu@<PUBLIC_IP>

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
                        docker-buildx-plugin docker-compose-plugin

# Add ubuntu to docker group (no sudo needed)
sudo usermod -aG docker ubuntu
newgrp docker

# Create app directory
mkdir -p ~/app

# Verify
docker --version
docker compose version
```

Copy the production Compose file to the server:
```bash
scp docker-compose.prod.yml ubuntu@<PUBLIC_IP>:~/app/docker-compose.prod.yml
```

---

### Step 5 — Configure GitHub Secrets

Go to your GitHub repository → **Settings → Secrets and variables → Actions → New repository secret**.

| Secret Name          | Value                                                      |
|----------------------|------------------------------------------------------------|
| `SERVER_HOST`        | Public IP of your cloud server (e.g., `159.89.x.x`)       |
| `SERVER_USER`        | SSH username (`ubuntu` for DigitalOcean / AWS Ubuntu AMI)  |
| `SSH_PRIVATE_KEY`    | Full content of `~/.ssh/id_rsa_deploy` (private key)       |
| `DOCKERHUB_USERNAME` | Your Docker Hub username                                   |
| `DOCKERHUB_TOKEN`    | Docker Hub Access Token (Settings → Security → New Token)  |

> [!CAUTION]
> **Never** commit private keys or tokens into your repository. Always use GitHub Secrets.

---

### Step 6 — Trigger the CD Pipeline

```bash
# Push to main branch → triggers cd.yml automatically
git add .
git commit -m "feat(workshop12): add cloud deployment pipeline"
git push origin main
```

Watch the pipeline at:
`https://github.com/<YOUR_ORG>/<YOUR_REPO>/actions`

The pipeline runs two jobs in sequence:
1. **build-and-push** — builds the Docker image and pushes to Docker Hub
2. **deploy-to-server** — SSHes into the cloud server, pulls the new image, restarts the container

---

### Step 7 — Verify the Deployment

```bash
# Hit the health endpoint from your local machine
curl http://<PUBLIC_IP>:8000/health

# Expected response:
# {"status":"ok","message":"Hello Sakon Nakhon Cloud!"}
```

You can also open it in a browser:
`http://<PUBLIC_IP>:8000/health`

Check the API docs:
`http://<PUBLIC_IP>:8000/api/v1/docs`

---

## 🔑 Quick Reference — GitHub Secrets Checklist

```
✅  SERVER_HOST          – Cloud server public IP
✅  SERVER_USER          – ubuntu
✅  SSH_PRIVATE_KEY      – Content of id_rsa_deploy (private key)
✅  DOCKERHUB_USERNAME   – Docker Hub username
✅  DOCKERHUB_TOKEN      – Docker Hub access token
```

---

## 🗺️ Architecture Overview

```
Developer Machine
     │
     │  git push → main
     ▼
GitHub Actions
  ┌─────────────────────┐      ┌───────────────────────────┐
  │  Job 1              │      │  Job 2                    │
  │  build-and-push     │─────▶│  deploy-to-server         │
  │  ─────────────────  │      │  ────────────────────────  │
  │  docker build       │      │  SSH → Cloud Server       │
  │  docker push        │      │  docker pull              │
  │  → Docker Hub       │      │  docker compose up -d     │
  └─────────────────────┘      │  curl /health ✅          │
                               └───────────────────────────┘
                                          │
                                          ▼
                               Cloud Server (Ubuntu 22.04)
                               ┌──────────────────────────┐
                               │  Docker Container        │
                               │  iot-api:latest          │
                               │  Port 8000               │
                               │  GET /health → 200 OK    │
                               └──────────────────────────┘
```

---

## 🧹 Tear Down

```bash
# Destroy the cloud server (stops billing)
cd infrastructure/
terraform destroy -var="do_token=..." -var="ssh_key_fingerprint=..."
```
