# Milestone 7: AWS Private Service Deployment

## Networking Concept

After the VPC foundation exists, the next step is placing service workloads into private subnets and registering them behind the internal load balancer. This models a distributed analytics platform where clients use a private service endpoint while individual nodes remain unreachable from the public internet.

This milestone adds an opt-in ECS/Fargate deployment layer:

- Three private dbnode services: `node-a`, `node-b`, and `node-c`.
- One Fargate task per node service.
- Tasks register to the internal ALB target group.
- Tasks use the private service-node security group.
- Tasks do not receive public IPs.
- CloudWatch Logs captures container stdout/stderr.

## Proposed Folder Structure

```text
.
├── docs/milestones/07-aws-service-deployment.md
├── infra/terraform/aws
│   ├── README.md
│   ├── ecs.tf
│   ├── outputs.tf
│   └── variables.tf
└── tests/terraform/test_aws_network_foundation.py
```

## Implemented Feature

This milestone adds Terraform for:

- ECS cluster.
- ECS task execution role.
- Three Fargate task definitions with node-specific environment variables.
- Three ECS services, one per simulated dbnode.
- Internal ALB target group registration for each service.
- CloudWatch Logs group for dbnode tasks.
- Optional VPC endpoints for private image pulls and log writes:
  - ECR API endpoint.
  - ECR Docker endpoint.
  - CloudWatch Logs endpoint.
  - S3 gateway endpoint for ECR layer downloads.

The deployment is disabled by default:

```hcl
enable_service_deployment = false
```

This keeps the default plan low-cost and lets you review the network separately from running compute.

## Image Requirement

To deploy ECS tasks, first build and push the dbnode image to a registry ECS can pull from, normally ECR:

```bash
aws ecr create-repository --repository-name netscope-dbnode --profile dev
aws ecr get-login-password --profile dev | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker build -f services/dbnode/Dockerfile -t netscope-dbnode .
docker tag netscope-dbnode:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest
```

Replace `ACCOUNT_ID` and region as needed.

## Cost Controls

Defaults:

```hcl
enable_service_deployment          = false
enable_nat_gateway                 = false
enable_private_image_pull_endpoints = false
```

The ECS services use:

```hcl
deployment_minimum_healthy_percent = 0
deployment_maximum_percent         = 100
```

That is a lab cost tradeoff. It allows replacement deployments without temporarily running extra Fargate tasks, but it can create a brief service interruption during deployment. A production deployment should raise the minimum healthy percentage and allow surge capacity.

When ECS deployment is enabled with NAT disabled, tasks need private AWS service endpoints to pull from ECR and write CloudWatch Logs:

```bash
terraform -chdir=infra/terraform/aws plan \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

Those interface endpoints have hourly charges. An alternative is enabling the NAT gateway, which also has hourly charges. Destroy resources when you finish testing.

## Automated Tests

Run:

```bash
uv run pytest
terraform -chdir=infra/terraform/aws fmt -check
terraform -chdir=infra/terraform/aws validate
```

The tests verify:

- ECS deployment is opt-in.
- Services run in private subnets.
- ECS tasks do not receive public IPs.
- Three named node services are declared.
- Services register with the internal ALB target group.
- CloudWatch logging and private image-pull endpoint controls exist.

## Manual Verification

Review the default low-cost plan:

```bash
terraform -chdir=infra/terraform/aws plan
```

Review a private ECS deployment plan:

```bash
terraform -chdir=infra/terraform/aws plan \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

Apply only when you are ready to create AWS resources:

```bash
terraform -chdir=infra/terraform/aws apply \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

After apply, check ECS service state:

```bash
aws ecs list-services --cluster netscope-lab-cluster --profile dev
terraform -chdir=infra/terraform/aws output service_target_group_arn
aws elbv2 describe-target-health --target-group-arn TARGET_GROUP_ARN --profile dev
```

Destroy everything:

```bash
terraform -chdir=infra/terraform/aws destroy \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

## Expected Result

The default plan should keep compute disabled. The deployment plan should add private ECS/Fargate dbnode services that register with the internal ALB, write logs to CloudWatch, and remain inaccessible from the public internet.
