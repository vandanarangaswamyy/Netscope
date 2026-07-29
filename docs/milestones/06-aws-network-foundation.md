# Milestone 6: AWS Network Foundation

## Networking Concept

Cloud reliability starts with clear network boundaries. A production-style distributed analytics platform should keep service nodes private, expose stable internal endpoints, and capture network telemetry for troubleshooting.

This milestone builds the AWS foundation for that model:

- Public subnets hold edge networking resources such as an internet gateway and optional NAT gateway.
- Private subnets hold internal service-facing resources.
- An internal application load balancer provides a stable private endpoint.
- Private Route 53 DNS maps a service name to the internal load balancer.
- Security groups restrict service-node ingress to the internal load balancer.
- VPC Flow Logs send accepted and rejected traffic metadata to CloudWatch Logs.

## Proposed Folder Structure

```text
.
├── docs/milestones/06-aws-network-foundation.md
├── infra/terraform/aws
│   ├── README.md
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   └── versions.tf
└── tests/terraform/test_aws_network_foundation.py
```

## Implemented Feature

This milestone adds Terraform for:

- VPC with DNS support and DNS hostnames enabled.
- Two public subnets across two availability zones.
- Two private subnets across two availability zones.
- Public route table with internet gateway route.
- Private route table with optional NAT gateway default route.
- NAT gateway resources gated by `enable_nat_gateway`.
- Internal application load balancer in private subnets.
- Target group and listener for future service-node registration.
- Private Route 53 hosted zone and internal alias record.
- Security group for the internal load balancer.
- Security group for private service nodes.
- VPC Flow Logs to CloudWatch Logs with 7-day retention.

## Cost Controls

The default plan keeps NAT disabled:

```hcl
enable_nat_gateway = false
```

This avoids NAT gateway hourly charges during early lab work. Enable it only when private resources need outbound internet access:

```bash
terraform plan -var='enable_nat_gateway=true'
```

Flow logs remain enabled by default because rejected-traffic visibility is core to this lab. Retention defaults to 7 days.

## Automated Tests

Run from the repository root:

```bash
uv run pytest
terraform -chdir=infra/terraform/aws fmt -check
```

The Python tests verify:

- Required AWS resource declarations exist.
- The foundation uses two public and two private subnets.
- NAT gateway creation is disabled by default.
- The load balancer is internal.
- Private service nodes only accept load balancer ingress.
- Flow logs default to enabled with short retention.

## Manual Verification

Review Terraform formatting:

```bash
terraform -chdir=infra/terraform/aws fmt -check
```

Initialize Terraform:

```bash
terraform -chdir=infra/terraform/aws init
```

Review the low-cost default plan:

```bash
terraform -chdir=infra/terraform/aws plan
```

Review the full plan with NAT:

```bash
terraform -chdir=infra/terraform/aws plan -var='enable_nat_gateway=true'
```

Apply only when you are ready to create AWS resources:

```bash
terraform -chdir=infra/terraform/aws apply
```

Destroy everything created by this stack:

```bash
terraform -chdir=infra/terraform/aws destroy
```

## Expected Result

The default plan should show a removable AWS network foundation with no public access to service nodes. The internal load balancer and private DNS are created for later service deployment, and VPC Flow Logs provide the CloudWatch-backed rejected-traffic data needed by later diagnostics.
