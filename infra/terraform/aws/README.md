# AWS Network Foundation

This Terraform stack creates the AWS network foundation for the Netscope lab.

## What It Creates

- One VPC with DNS support enabled.
- Two public subnets across two availability zones.
- Two private subnets across the same two availability zones.
- Public and private route tables.
- Internet gateway for public subnet routing.
- Optional NAT gateway for private outbound internet access.
- Security groups for an internal load balancer and private service nodes.
- Internal application load balancer in private subnets.
- Empty target group for future service-node registration.
- Private Route 53 hosted zone and internal service alias.
- VPC Flow Logs to CloudWatch Logs.
- Optional private ECS/Fargate service deployment for three dbnode tasks.
- Optional VPC endpoints for private ECR image pulls and CloudWatch Logs writes without NAT.
- Optional Terraform-managed ECR repository for dbnode images.

## Cost Defaults

The NAT gateway is disabled by default:

```hcl
enable_nat_gateway = false
```

Set it to `true` only when the private subnets need outbound internet access. NAT gateways have hourly and data processing charges.

Flow logs are enabled by default with 7-day retention.

ECS service deployment is disabled by default:

```hcl
enable_service_deployment = false
```

When enabled, it creates three private Fargate services with one task each. Tasks are registered to the internal load balancer and are not assigned public IPs.

The ECS service deployment policy uses `deployment_minimum_healthy_percent = 0` and `deployment_maximum_percent = 100`. This is a lab cost tradeoff that avoids temporarily running extra Fargate tasks during replacements. It may cause brief interruption during a deployment and should be adjusted upward for production.

ECR repository creation is disabled by default:

```hcl
enable_ecr_repository = false
```

Enable it when you want Terraform to manage the dbnode image repository and lifecycle policy.

## Commands

Initialize:

```bash
cd infra/terraform/aws
terraform init
```

Review the low-cost default plan:

```bash
terraform plan
```

Review the full network plan with NAT:

```bash
terraform plan -var='enable_nat_gateway=true'
```

Review the private ECS service deployment plan:

```bash
terraform plan \
  -var='enable_service_deployment=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

Review Terraform-managed ECR creation:

```bash
terraform plan -var='enable_ecr_repository=true'
```

If NAT stays disabled, enable private AWS service endpoints for ECR image pulls and CloudWatch Logs:

```bash
terraform plan \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:latest'
```

Apply:

```bash
terraform apply
```

Destroy all resources:

```bash
terraform destroy
```

## Security Notes

- The load balancer is internal.
- Service node security group ingress only allows traffic from the internal load balancer security group.
- Public subnets do not assign public IPs on launch by default.
- No service node ports are exposed publicly.
- ECS tasks run in private subnets with `assign_public_ip = false`.
