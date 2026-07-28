# AWS RDS Deployment Guide — Banking Support Agent

This document records the AWS deployment process used for the `banking-support-agent` project after adding persistent PostgreSQL workflow storage.

The application was containerised with Docker, pushed to Amazon Elastic Container Registry, deployed on Amazon Elastic Container Service with AWS Fargate, connected to a private Amazon RDS for PostgreSQL database, migrated with Alembic, validated through public API/UI endpoints, and then cleaned up to avoid leaving unnecessary cloud resources running.

This guide is separate from `DEPLOYMENT.md`, which records the earlier deployment without RDS persistence.

---

## 1. Deployment Summary

### Application

```text
Project: banking-support-agent
Framework: FastAPI
Runtime: Docker container
UI route: /ui
Health route: /health
Main API route: /support
Workflow storage: Amazon RDS for PostgreSQL
AWS Region: eu-west-2, Europe (London)
```

### Final AWS deployment path

```text
Local code
↓
Docker image
↓
Amazon Elastic Container Registry
↓
Amazon Elastic Container Service
↓
AWS Fargate task
↓
Application Load Balancer
↓
FastAPI application
↓
AWS Secrets Manager
↓
Private Amazon RDS for PostgreSQL
```

### What this deployment proves

```text
The FastAPI app can run as a cloud container.
The Docker image can be stored and reused from Amazon ECR.
Runtime secrets can be injected securely through AWS Secrets Manager.
The app can use PostgreSQL instead of in-memory workflow storage.
Private RDS access can be restricted to the ECS task security group.
Alembic migrations can be run as a one-off ECS task.
The live app can create and read persisted workflow records.
```

---

## 2. AWS Services Used

| Service | Full form | Purpose in this deployment |
|---|---|---|
| AWS IAM | AWS Identity and Access Management | Controlled users, roles, and permissions |
| Amazon ECR | Amazon Elastic Container Registry | Stored the Docker image used by ECS |
| Amazon ECS | Amazon Elastic Container Service | Ran the containerised FastAPI application |
| AWS Fargate | AWS Fargate | Ran containers without manually managing EC2 instances |
| ALB | Application Load Balancer | Public HTTP entry point for the deployed app |
| Amazon RDS | Amazon Relational Database Service | Hosted the PostgreSQL database |
| PostgreSQL | PostgreSQL relational database | Persisted workflow and workflow event records |
| AWS Secrets Manager | AWS Secrets Manager | Stored `GEMINI_API_KEY` and `DATABASE_URL` securely |
| Amazon CloudWatch | Amazon CloudWatch | Stored ECS task and migration logs |
| Amazon VPC | Amazon Virtual Private Cloud | Provided network isolation and security group control |
| AWS CLI | AWS Command Line Interface | Used to create and verify deployment resources |

---

## 3. Repository Structure


```text
banking-support-agent/
  cloud_deployment_docs/
    aws/
      DEPLOYMENT.md
      DEPLOYMENT_RDS.md
      screenshots/
      screenshots_rds/
        01_health_endpoint.png
        02_UI_endpoint.png
        03_workflow_persistence.png
        04_ECS_service_running.png
        05_ECS_service_utilizations.png
        06_ECS_Task_Def_overview.png
        07_ECS_Task_Def_env_secrets.png
        08_RDS_overview.png
        09_RDS_no_public_access.png
        10_RDS_security_group_inbound_rule.png
        11_CloudWatch_logs.png
        12_ECR_tagged_image.png
```

---

## 4. Local Prerequisites

The deployment used:

```text
Windows 11
Git Bash
Docker Desktop
AWS CLI
Python virtual environment
```

Basic checks:

```bash
aws --version
docker --version
docker ps
```

The AWS CLI was configured with a named local profile.

Example:

```bash
aws configure --profile <aws-profile-name>
```

Common environment variables used during deployment:

```bash
export AWS_PROFILE=<aws-profile-name>
export AWS_REGION=eu-west-2
export REPO_NAME=banking-support-agent
export IMAGE_TAG=rds-postgres-demo-v1
```

Identity check:

```bash
aws sts get-caller-identity --profile $AWS_PROFILE
```

`STS` means `Security Token Service`. This command confirms which AWS identity the CLI is using.

---

## 5. Application Database Upgrade

The project was upgraded from in-memory workflow storage to PostgreSQL-backed workflow storage.

Main database components:

```text
SQLAlchemy = Python ORM/database layer
Alembic = database migration tool
psycopg = PostgreSQL database driver
Amazon RDS = managed PostgreSQL database host
```

The application supports two workflow storage modes:

```text
WORKFLOW_STORAGE_BACKEND=memory
WORKFLOW_STORAGE_BACKEND=postgres
```

For the AWS RDS deployment, the application used:

```text
WORKFLOW_STORAGE_BACKEND=postgres
DATABASE_URL=<Secrets Manager value>
```

The `DATABASE_URL` was not committed to the repository and was not stored directly in the Docker image.

---

## 6. Docker Image Preparation

The Docker image included the application code, runtime dependencies, and Alembic migration files.

Important Dockerfile behaviour:

```dockerfile
CMD ["sh", "-c", "python -m uvicorn banking_agent.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Meaning:

```text
0.0.0.0 = listen on all container network interfaces
${PORT:-8000} = use the cloud-provided PORT if present, otherwise default to 8000
```

The image also needed these files inside the container:

```text
src/
alembic.ini
alembic/
requirements-docker.txt
```

This mattered because the same image was used for both:

```text
1. the long-running FastAPI web service
2. the one-off Alembic database migration task
```

Local build:

```bash
DOCKER_BUILDKIT=1 docker build -t "$REPO_NAME:$IMAGE_TAG" .
```

Local smoke test in memory mode:

```bash
docker run --rm --name banking-support-agent-smoke \
  -e WORKFLOW_STORAGE_BACKEND=memory \
  -p 8001:8000 \
  banking-support-agent:rds-postgres-demo-v1
```

Validation:

```bash
curl --fail http://127.0.0.1:8001/health
curl --fail http://127.0.0.1:8001/ui
```

---

## 7. Amazon ECR Image Push

`Amazon ECR` means `Amazon Elastic Container Registry`. It stores private Docker images in AWS so ECS can pull and run them.

Set ECR variables:

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity \
  --profile $AWS_PROFILE \
  --query Account \
  --output text)

export ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
export ECR_URI="$ECR_REGISTRY/$REPO_NAME"
```

The full `ECR_URI` contains the AWS account ID and should not be committed publicly.

Authenticate Docker to ECR:

```bash
aws ecr get-login-password \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  | docker login \
    --username AWS \
    --password-stdin $ECR_REGISTRY
```

Tag image:

```bash
docker tag "$REPO_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker tag "$REPO_NAME:$IMAGE_TAG" "$ECR_URI:latest"
```

Push image:

```bash
docker push "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:latest"
```

Verify image:

```bash
aws ecr describe-images \
  --repository-name $REPO_NAME \
  --image-ids imageTag=$IMAGE_TAG \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  --query 'imageDetails[0].{Tags:imageTags,PushedAt:imagePushedAt,Size:imageSizeInBytes}'
```

Expected result:

```text
Image tags include:
- rds-postgres-demo-v1
- latest
```

Evidence screenshot:

![ECR tagged image](screenshots_rds/12_ECR_tagged_image.png)

---

## 8. Amazon RDS PostgreSQL Setup

A private PostgreSQL database was created through Amazon RDS.

RDS configuration used:

```text
Engine: PostgreSQL
Deployment: Single-AZ DB instance
Instance class: db.t4g.micro
Storage: 20 GiB General Purpose SSD
Network type: IPv4
Public access: No
Initial database name: banking_agent
Deletion protection: Off
Backup retention: 1 day
```

The database was created for a short deployment proof and then deleted after screenshots and validation.

Evidence screenshots:

![RDS overview](screenshots_rds/08_RDS_overview.png)

![RDS no public access](screenshots_rds/09_RDS_no_public_access.png)

---

## 9. RDS Security Group Design

The RDS database was not made public.

The intended traffic path was:

```text
Internet
↓
Application Load Balancer security group
↓
ECS task security group
↓
RDS security group
↓
PostgreSQL port 5432
```

Security group pattern:

```text
ALB security group:
  inbound HTTP 80 from 0.0.0.0/0

ECS task security group:
  inbound TCP 8000 from ALB security group

RDS security group:
  inbound PostgreSQL TCP 5432 from ECS task security group only
```

The RDS security group did not allow:

```text
0.0.0.0/0
public laptop IP access
Anywhere IPv4
```

This means the database endpoint existed, but direct access from the public internet was blocked.

Evidence screenshot:

![RDS security group inbound rule](screenshots_rds/10_RDS_security_group_inbound_rule.png)

---

## 10. AWS Secrets Manager Configuration

Two runtime secrets were used.

```text
GEMINI_API_KEY
DATABASE_URL
```

### Gemini API key secret

```text
Secret name: banking-support-agent/gemini-api-key
Secret format: plaintext
Stored value: raw Gemini API key only
```

Correct value format:

```text
AIza...actual_key...
```

Incorrect value format:

```text
GEMINI_API_KEY=AIza...
```

### Database URL secret

```text
Secret name: banking-support-agent/database-url
Secret format: plaintext
Stored value: full SQLAlchemy PostgreSQL connection string
```

Expected format:

```text
postgresql+psycopg://<username>:<password>@<rds-endpoint>:5432/banking_agent
```

The `DATABASE_URL` secret was deleted after the RDS database was deleted because it was no longer useful and still contained sensitive connection information.

---

## 11. ECS Task Definition

A new task definition was created instead of reusing the earlier non-RDS deployment task definition.

Task definition configuration:

```text
Family: banking-support-agent-rds
Launch type: AWS Fargate
CPU: 0.25 vCPU
Memory: 0.5 GB
Operating system: Linux
CPU architecture: X86_64
Network mode: awsvpc
Container name: banking-support-agent
Container port: 8000
```

Plain environment variables:

```text
APP_NAME=Banking Support Agent
ENVIRONMENT=production
WORKFLOW_STORAGE_BACKEND=postgres
GEMINI_MODEL=gemini-2.5-flash
```

Secret environment variables:

```text
GEMINI_API_KEY=<Secrets Manager secret reference>
DATABASE_URL=<Secrets Manager secret reference>
```

The task definition did not include a command override. The normal command remained the Dockerfile command that starts the FastAPI app.

Evidence screenshots:

![ECS task definition overview](screenshots_rds/06_ECS_Task_Def_overview.png)

![ECS task definition environment and secrets](screenshots_rds/07_ECS_Task_Def_env_secrets.png)

---

## 12. ECS Task Execution Role

The ECS task execution role was required so ECS/Fargate could start the container.

It allowed ECS to:

```text
pull the image from Amazon ECR
write logs to CloudWatch
read configured Secrets Manager secrets
```

The application itself did not need a separate task role for this deployment because the Python code did not directly call AWS services. It read environment variables provided by ECS and connected to PostgreSQL using `DATABASE_URL`.

The task execution role needed permission to read both Secrets Manager secrets.

Policy shape:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadBankingSupportAgentSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "PASTE_GEMINI_SECRET_ARN_HERE",
        "PASTE_DATABASE_URL_SECRET_ARN_HERE"
      ]
    }
  ]
}
```

The actual ARNs were not committed or shown publicly.

---

## 13. One-Off Alembic Migration Task

The database schema was created before the live web service was used.

Instead of running migrations inside the normal application startup command, a one-off ECS task was used.

Command override:

```bash
python -m alembic upgrade head
```

Reason for a separate migration task:

```text
The app service should only start the web app.
The migration task should run once, update the database schema, and exit.
This avoids coupling schema migration to every application startup.
It is closer to a production-style deployment pattern.
```

The migration task used the same ECS task definition and same Docker image, but overrode the container command.

Successful migration log:

```text
[alembic.runtime.migration] Running upgrade  -> 001_create_workflow_tables, create workflow tables
```

Evidence screenshot:

![CloudWatch migration logs](screenshots_rds/11_CloudWatch_logs.png)

---

## 14. ECS Service and Load Balancer Deployment

After the migration succeeded, the live ECS service was created.

Service configuration:

```text
Cluster: banking-support-agent-cluster
Service name: banking-support-agent-service
Task definition: banking-support-agent-rds
Desired count: 1
Launch type: Fargate
Container port: 8000
Target group port: 8000
Load balancer listener: HTTP 80
Health check path: /health
```

The Application Load Balancer handled public HTTP traffic and forwarded it to the ECS task.

Runtime path:

```text
Public browser/curl request
↓
Application Load Balancer on port 80
↓
Target group on port 8000
↓
ECS Fargate task on port 8000
↓
FastAPI application
↓
Private RDS PostgreSQL
```

Evidence screenshots:

![ECS service running](screenshots_rds/04_ECS_service_running.png)

![ECS service utilization](screenshots_rds/05_ECS_service_utilizations.png)

---

## 15. Live Endpoint Validation

### Health endpoint

The deployed health endpoint returned a successful production response.

```bash
curl --fail "http://<alb-dns>/health"
```

Observed response:

```json
{
  "status": "ok",
  "app_name": "Banking Support Agent",
  "environment": "production"
}
```

Evidence screenshot:

![Health endpoint](screenshots_rds/01_health_endpoint.png)

### UI endpoint

The browser UI loaded successfully through the public Application Load Balancer URL.

```text
http://<alb-dns>/ui
```

A `GET` request returned HTTP `200`.

Evidence screenshot:

![UI endpoint](screenshots_rds/02_UI_endpoint.png)

### Workflow creation

A deterministic support request was sent to the deployed app.

```bash
curl -s -X POST "http://<alb-dns>/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "I was charged twice for transaction TX1001. Please help me raise a dispute.",
    "use_llm": false,
    "confirm_action": false
  }'
```

Expected response fields:

```text
workflow_id = WF-...
workflow_status = awaiting_confirmation
requires_confirmation = true
risk_level = low
security_flags = []
```

### Workflow persistence check

The persisted workflow records were retrieved from the deployed app:

```bash
curl -s "http://<alb-dns>/workflows"
```

Expected result:

```text
The endpoint returns workflow records from PostgreSQL-backed storage.
Records include workflow IDs, issue types, transaction IDs, statuses, timestamps, and ticket IDs where completed.
```

Evidence screenshot:

![Workflow persistence](screenshots_rds/03_workflow_persistence.png)

---

## 16. Debugging Notes

### Git Bash path conversion

Git Bash can sometimes convert values that start with `/` into Windows-style paths before passing them to AWS CLI.

This affected values such as:

```text
/health
/ecs/banking-support-agent-rds
```

The fix was to prefix affected AWS CLI commands with:

```bash
MSYS_NO_PATHCONV=1
```

Example:

```bash
MSYS_NO_PATHCONV=1 aws logs describe-log-streams \
  --log-group-name "/ecs/banking-support-agent-rds" \
  --region $AWS_REGION \
  --profile $AWS_PROFILE
```

### UI endpoint and HEAD requests

The command below sends a `HEAD` request:

```bash
curl -I "http://<alb-dns>/ui"
```

The app returned:

```text
405 Method Not Allowed
allow: GET
```

This was not a deployment failure. The `/ui` route supports `GET`, so it was validated with:

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://<alb-dns>/ui"
```

Expected result:

```text
200
```

### RDS direct access from laptop

Direct RDS access from the local laptop was intentionally not allowed.

Reason:

```text
RDS public access = No
RDS inbound rule = PostgreSQL 5432 from ECS security group only
```

This is expected for a private database deployment.

---

## 17. Cleanup and Cost Control

After validation and screenshots, the deployment was cleaned up to avoid leaving paid resources running.

Deleted resources:

```text
ECS service
ECS cluster used for this deployment
RDS PostgreSQL database instance
Application Load Balancer listener
Application Load Balancer
Target group
custom ALB security group
custom ECS task security group
custom RDS security group
DATABASE_URL secret
new RDS task definition revision
```

Kept intentionally:

```text
Amazon ECR repository
Docker image tags: rds-postgres-demo-v1 and latest
Gemini API key secret
CloudWatch logs with short retention
AWS budget alerts
screenshots and deployment documentation
```

The `DATABASE_URL` secret was deleted because the database was deleted and the connection string was no longer useful.

The Gemini API key secret was kept because it may be reused for later deployments.

The ECR image was kept because it is useful evidence of the deployment and can be reused without rebuilding.

---

## 18. Redeployment Checklist

To redeploy the RDS-backed version later:

### 1. Rebuild and push image

```bash
export AWS_PROFILE=<aws-profile-name>
export AWS_REGION=eu-west-2
export REPO_NAME=banking-support-agent
export IMAGE_TAG=rds-postgres-demo-v1

export ACCOUNT_ID=$(aws sts get-caller-identity \
  --profile $AWS_PROFILE \
  --query Account \
  --output text)

export ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
export ECR_URI="$ECR_REGISTRY/$REPO_NAME"

DOCKER_BUILDKIT=1 docker build -t "$REPO_NAME:$IMAGE_TAG" .

docker tag "$REPO_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker tag "$REPO_NAME:$IMAGE_TAG" "$ECR_URI:latest"

aws ecr get-login-password \
  --region $AWS_REGION \
  --profile $AWS_PROFILE \
  | docker login \
    --username AWS \
    --password-stdin $ECR_REGISTRY

docker push "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:latest"
```

### 2. Recreate RDS PostgreSQL

Use a private RDS PostgreSQL DB instance:

```text
Engine: PostgreSQL
Instance class: micro/sandbox class for demo use
Initial database name: banking_agent
Public access: No
Security group: allow PostgreSQL 5432 only from ECS task security group
```

### 3. Recreate DATABASE_URL secret

```text
Secret name: banking-support-agent/database-url
Secret value: postgresql+psycopg://<username>:<password>@<rds-endpoint>:5432/banking_agent
```

Do not commit the connection string.

### 4. Create or update ECS task definition

Required plain environment variables:

```text
APP_NAME=Banking Support Agent
ENVIRONMENT=production
WORKFLOW_STORAGE_BACKEND=postgres
GEMINI_MODEL=gemini-2.5-flash
```

Required secret environment variables:

```text
GEMINI_API_KEY=<Secrets Manager reference>
DATABASE_URL=<Secrets Manager reference>
```

### 5. Run Alembic migration task

Run a one-off ECS task with command override:

```bash
python -m alembic upgrade head
```

Verify CloudWatch logs show the migration completed successfully.

### 6. Create ECS service and ALB

Create the ECS service after the migration task succeeds.

```text
Desired tasks: 1
Container port: 8000
ALB listener: HTTP 80
Target group health check: /health
```

### 7. Validate endpoints

```bash
curl --fail "http://<alb-dns>/health"
curl -s -o /dev/null -w "%{http_code}\n" "http://<alb-dns>/ui"
curl -s "http://<alb-dns>/workflows"
```

---

## 19. Current Limitations

This was a portfolio-grade cloud deployment, not a full production banking deployment.

Current limitations:

```text
No custom domain
No HTTPS certificate configured for the demo ALB endpoint
No production authentication
No role-based access control
No Terraform or Infrastructure as Code
No blue/green deployment strategy
No production autoscaling policy
Single demo database instance, not high availability
Mock banking tools and mock transaction data
No real core banking integration
```

Production improvements would include:

```text
Infrastructure as Code with Terraform or AWS CDK
separate dev/staging/prod environments
private subnets and NAT or VPC endpoints
HTTPS with AWS Certificate Manager
authentication and role-based access control
monitoring alarms and dashboards
database backups and migration runbooks
least-privilege IAM policies
centralised audit logging
```

---

## 20. Official References

- Amazon ECR: Pushing a Docker image to an Amazon ECR private repository  
  https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html

- Amazon ECS task execution IAM role  
  https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html

- Amazon ECS services  
  https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html

- Amazon ECS standalone tasks  
  https://docs.aws.amazon.com/AmazonECS/latest/developerguide/standalone-task-create.html

- Amazon ECS Fargate tasks and services  
  https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html

- Amazon ECS secrets as environment variables  
  https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html

- Amazon RDS: Creating a PostgreSQL DB instance  
  https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.PostgreSQL.html

- Amazon RDS: Public and private database access  
  https://docs.aws.amazon.com/AmazonRDS/latest/gettingstartedguide/security-public-private.html

- Amazon RDS: Working with a DB instance in a VPC  
  https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html

- Amazon RDS: Deleting a DB instance  
  https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html

- CloudWatch Logs retention policy  
  https://docs.aws.amazon.com/cli/latest/reference/logs/put-retention-policy.html
