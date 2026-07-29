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

variable "github_owner_id" {
  description = "Immutable GitHub owner ID from the repository OIDC customization API."
  type        = string
  default     = "181282565"

  validation {
    condition     = can(regex("^[0-9]+$", var.github_owner_id))
    error_message = "github_owner_id must contain only digits."
  }
}

variable "github_repository" {
  description = "GitHub repository name."
  type        = string
  default     = "Netscope"
}

variable "github_repository_id" {
  description = "Immutable GitHub repository ID from the repository OIDC customization API."
  type        = string
  default     = "1308859104"

  validation {
    condition     = can(regex("^[0-9]+$", var.github_repository_id))
    error_message = "github_repository_id must contain only digits."
  }
}

variable "github_branch" {
  description = "Git branch allowed to assume the role."
  type        = string
  default     = "main"

  validation {
    condition     = !strcontains(var.github_branch, "*") && !strcontains(var.github_branch, "?")
    error_message = "github_branch must be exact and must not contain wildcards."
  }
}

variable "github_subject_claim_prefix" {
  description = "GitHub OIDC sub claim prefix returned by the repository OIDC customization API."
  type        = string
  default     = "repo:vandanarangaswamyy@181282565/Netscope@1308859104"

  validation {
    condition     = var.github_subject_claim_prefix == "repo:${var.github_owner}@${var.github_owner_id}/${var.github_repository}@${var.github_repository_id}"
    error_message = "github_subject_claim_prefix must match repo:<owner>@<owner_id>/<repo>@<repo_id> from the explicit variables."
  }

  validation {
    condition     = !strcontains(var.github_subject_claim_prefix, "*") && !strcontains(var.github_subject_claim_prefix, "?")
    error_message = "github_subject_claim_prefix must be exact and must not contain wildcards."
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
