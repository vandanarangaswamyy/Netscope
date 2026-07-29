variable "project_name" {
  description = "Name prefix for IAM resources."
  type        = string
  default     = "netscope"
}

variable "aws_region" {
  description = "AWS region used for regional service ARNs such as ECR."
  type        = string
  default     = "us-east-1"
}

variable "github_owner" {
  description = "GitHub repository owner."
  type        = string
  default     = "vandanarangaswamyy"
}

variable "github_repository" {
  description = "GitHub repository name."
  type        = string
  default     = "Netscope"
}

variable "github_branch" {
  description = "Git branch allowed to assume the role."
  type        = string
  default     = "main"
}

variable "github_subject_claim" {
  description = "Exact GitHub OIDC sub claim allowed to assume the role. Override if GitHub uses immutable repository subject claims for this repo."
  type        = string
  default     = "repo:vandanarangaswamyy/Netscope:ref:refs/heads/main"

  validation {
    condition     = !strcontains(var.github_subject_claim, "*") && !strcontains(var.github_subject_claim, "?")
    error_message = "github_subject_claim must be exact and must not contain wildcards."
  }
}

variable "github_oidc_provider_url" {
  description = "GitHub Actions OIDC issuer URL."
  type        = string
  default     = "https://token.actions.githubusercontent.com"
}

variable "existing_github_oidc_provider_arn" {
  description = "Existing GitHub Actions OIDC provider ARN to reuse. Leave empty to create one."
  type        = string
  default     = ""
}

variable "github_oidc_audience" {
  description = "Audience for AWS STS when using GitHub Actions OIDC."
  type        = string
  default     = "sts.amazonaws.com"
}

variable "role_name" {
  description = "IAM role name for GitHub Actions."
  type        = string
  default     = "netscope-github-actions-plan"
}

variable "ecr_repository_name" {
  description = "ECR repository name allowed for optional dbnode image push."
  type        = string
  default     = "netscope-dbnode"
}
