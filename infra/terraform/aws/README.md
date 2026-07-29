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

## Cost Defaults

The NAT gateway is disabled by default:

```hcl
enable_nat_gateway = false
```

Set it to `true` only when the private subnets need outbound internet access. NAT gateways have hourly and data processing charges.

Flow logs are enabled by default with 7-day retention.

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
