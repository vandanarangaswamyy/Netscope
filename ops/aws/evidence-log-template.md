# NetScope AWS Evidence Log

Use this template during the controlled same-day AWS deployment test.

## Run Metadata

```text
Date:
Operator:
AWS profile:
AWS account ID:
AWS region:
Git commit:
Image URI:
Terraform backup directory:
```

## Preflight

```text
uv run pytest:
terraform fmt:
terraform init:
terraform validate:
aws sts get-caller-identity:
git check-ignore terraform state:
git check-ignore saved plans:
git check-ignore backup dir:
Pre-apply state backup path:
```

## ECR Evidence

```text
ECR plan result:
ECR apply time:
ECR repository URL:
Image tag:
docker push result:
Build platform: expected linux/amd64
aws ecr describe-images summary:
Post-ECR state backup path:
```

## Infrastructure Evidence

```text
Private ECS plan result:
Apply start:
Apply end:
VPC ID:
Private subnet IDs:
Internal ALB DNS:
Private service FQDN:
Target group ARN:
Service node security group ID:
Post-ECS state backup path:
```

## ECS And ALB Health Evidence

```text
aws ecs wait services-stable result:
aws ecs describe-services summary:
aws elbv2 describe-target-health summary:
Healthy target count:
Unhealthy target count:
```

## Internal Connectivity Evidence

```text
Smoke task ARN:
Smoke task ARN nonempty and not None:
Smoke task stopped:
Smoke task describe-tasks summary:
Smoke task container exit code: expected 0
Smoke task subnet:
Smoke task public IP assigned: expected false
Smoke task command:
Smoke task result:
Internal service response summary:
```

## CloudWatch Evidence

```text
Application log group:
Recent dbnode log events summary:
Flow log group:
ACCEPT evidence summary:
REJECT evidence summary:
```

## Cost And Cleanup Evidence

```text
NAT gateway enabled: expected false
ECR image deletion result:
ECR image list after deletion: expected empty
Pre-destroy state backup path:
Destroy plan reviewed:
Destroy start:
Destroy end:
Post-destroy state backup path:
Remaining ECS clusters/services:
Remaining ECR repository check:
Remaining ALB check:
Remaining VPC endpoint check:
Remaining VPC check:
Remaining Route 53 private zone check:
Remaining CloudWatch app log group check:
Remaining VPC Flow Log group check:
Terraform state list after destroy: expected empty
Notes:
```
