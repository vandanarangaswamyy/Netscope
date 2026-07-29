output "vpc_id" {
  description = "ID of the lab VPC."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets."
  value       = aws_subnet.private[*].id
}

output "internal_load_balancer_dns_name" {
  description = "AWS DNS name of the internal application load balancer."
  value       = aws_lb.internal.dns_name
}

output "private_service_fqdn" {
  description = "Private Route 53 name for the service endpoint."
  value       = aws_route53_record.service.fqdn
}

output "service_node_security_group_id" {
  description = "Security group ID intended for private service nodes."
  value       = aws_security_group.service_nodes.id
}

output "service_target_group_arn" {
  description = "Target group ARN for private dbnode services."
  value       = aws_lb_target_group.service_nodes.arn
}

output "nat_gateway_enabled" {
  description = "Whether the optional NAT gateway was created."
  value       = var.enable_nat_gateway
}

output "vpc_flow_logs_log_group_name" {
  description = "CloudWatch log group for VPC Flow Logs, when enabled."
  value       = var.enable_flow_logs ? aws_cloudwatch_log_group.vpc_flow_logs[0].name : null
}

output "ecs_cluster_name" {
  description = "ECS cluster name when service deployment is enabled."
  value       = var.enable_service_deployment ? aws_ecs_cluster.this[0].name : null
}

output "ecs_service_names" {
  description = "ECS service names for deployed dbnodes."
  value       = var.enable_service_deployment ? [for service in aws_ecs_service.dbnode : service.name] : []
}

output "dbnode_log_group_name" {
  description = "CloudWatch log group for dbnode ECS tasks when enabled."
  value       = var.enable_service_deployment ? aws_cloudwatch_log_group.dbnode[0].name : null
}

output "dbnode_ecr_repository_url" {
  description = "URL of the optional Terraform-managed dbnode ECR repository."
  value       = var.enable_ecr_repository ? aws_ecr_repository.dbnode[0].repository_url : null
}
