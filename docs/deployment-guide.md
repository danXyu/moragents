# Deployment Guide

This document outlines the process for deploying the MySuperAgent platform and individual agents to production environments.

## Overview

MySuperAgent uses AWS CloudFormation for infrastructure as code (IaC) deployment, with GitHub Actions for CI/CD automation.

## Architecture

The platform consists of:

- **Frontend**: React application served via CloudFront
- **Backend**: Python FastAPI service running on EC2
- **Infrastructure**:
  - Application Load Balancer
  - EC2 instances
  - RDS database
  - S3 storage
  - ACM certificates for HTTPS
  - Route53 DNS configuration

## Prerequisites

Before deployment, ensure you have:

1. AWS account with appropriate permissions
2. GitHub repository access
3. Required secrets configured in GitHub repository

## Environment Setup

### AWS Resources

The following AWS resources should be set up:

1. **VPC**: `vpc-0e17a977e38b866c1`
2. **Subnets**:
   - `subnet-01abb34d1b3a008ac`
   - `subnet-0a852de834c421b24`
3. **Security Groups**:
   - ALB Security Group: `sg-0ab173f93f4f06ac1`
4. **Route53 Hosted Zone**: `Z08521642MAYLL3XZZMIN`
5. **EC2 Key Pair**: `agents-key`

## Deployment Process

### Infrastructure Deployment

To deploy or update the infrastructure, use the existing GitHub Actions workflow:

1. Navigate to the GitHub repository
2. Go to "Actions" tab
3. Select the "Deploy MySuperAgent Infrastructure" workflow
4. Click "Run workflow"
5. Choose the environment (staging/production)
6. Click "Run workflow" to execute

This workflow will deploy the CloudFormation stack defined in `infrastructure/moragents-stack.yml`.

### Agent Deployment

To build and push agent docker images to ECR:

1. Navigate to the GitHub repository
2. Go to "Actions" tab
3. Select the "Reusable Docker Production Build / Push (AWS ECR)" workflow
4. Click "Run workflow"
5. Provide the required inputs:
   - **app_directory**: Relative path to the application
   - **app_name**: Name of the application
   - **aws_account_id**: AWS account ID
   - **aws_region**: AWS region
   - **ecr_repository**: ECR repository name
   - **image_tag**: Version tag for the image
6. Click "Run workflow" to execute

The workflow will build and push the Docker image to ECR with the specified tag.

## Deployment Outputs

After successful deployment, the following outputs will be available:

- **Frontend URL**: `https://mysuperagent.io`
- **API URL**: `https://api.mysuperagent.io`
- **Load Balancer DNS**: Available in CloudFormation outputs

## Monitoring and Troubleshooting

### CloudWatch Monitoring

Monitor your deployment using:

- CloudWatch Alarms for EC2 instance health, API response time, and error rates
- CloudWatch Logs for application logs

### Emergency SSH Access

**Note**: SSH access should only be used for emergency troubleshooting when the application is not functioning properly and cannot be fixed through normal deployment methods.

If you need to access an EC2 instance directly:

```bash
ssh -i agents-key.pem ec2-user@<instance-public-ip>
```

The public IP is available in the CloudFormation outputs or EC2 console.

#### Emergency Docker Container Management

While SSH'd into the instance, you can:

View running containers:

```bash
docker ps
```

View container logs:

```bash
docker logs <container-id>
```

Restart containers:

```bash
docker restart <container-id>
```

Pull and run a specific image version:

```bash
docker pull <aws_account_id>.dkr.ecr.<region>.amazonaws.com/<repository>:<tag>
docker stop <container-id>
docker run -d --restart always -p 8888:5000 <aws_account_id>.dkr.ecr.<region>.amazonaws.com/<repository>:<tag>
```

**Important**: Any changes made via SSH should be temporary. Permanent changes should be made through the proper CI/CD pipeline.

## Security Considerations

1. **Security Groups**: Limit access to necessary ports only
2. **IAM Roles**: Use the principle of least privilege
3. **Secrets Management**: Store secrets in GitHub Secrets or AWS Secrets Manager
4. **HTTPS**: Ensure all traffic uses HTTPS
5. **Regular Updates**: Keep dependencies and OS up to date

## Adding New Agents

When adding a new agent to production:

1. Develop and test the agent locally
2. Submit a PR with comprehensive tests
3. After approval and merge to main, manually trigger the appropriate GitHub Actions workflow to build and deploy the new agent
