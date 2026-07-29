variable "project_name" {
  description = "Name prefix for AWS resources."
  type        = string
  default     = "netscope"
}

variable "environment" {
  description = "Environment label applied to resource names and tags."
  type        = string
  default     = "lab"
}

variable "aws_region" {
  description = "AWS region for the lab."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the lab VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Two public subnet CIDR blocks, one per availability zone."
  type        = list(string)
  default     = ["10.42.0.0/24", "10.42.1.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) == 2
    error_message = "Exactly two public subnet CIDRs are required."
  }
}

variable "private_subnet_cidrs" {
  description = "Two private subnet CIDR blocks, one per availability zone."
  type        = list(string)
  default     = ["10.42.10.0/24", "10.42.11.0/24"]

  validation {
    condition     = length(var.private_subnet_cidrs) == 2
    error_message = "Exactly two private subnet CIDRs are required."
  }
}

variable "private_dns_zone_name" {
  description = "Private Route 53 zone name for internal service discovery."
  type        = string
  default     = "netscope.local"
}

variable "service_dns_name" {
  description = "Internal DNS record name for the load-balanced analytics endpoint."
  type        = string
  default     = "analytics"
}

variable "service_port" {
  description = "Internal load balancer listener port."
  type        = number
  default     = 8080
}

variable "node_port" {
  description = "Private service node target port."
  type        = number
  default     = 8000
}

variable "enable_nat_gateway" {
  description = "Create a NAT gateway and private default route. Disabled by default to avoid hourly NAT cost."
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs to CloudWatch Logs."
  type        = bool
  default     = true
}

variable "flow_log_retention_days" {
  description = "CloudWatch retention period for VPC Flow Logs."
  type        = number
  default     = 7
}
