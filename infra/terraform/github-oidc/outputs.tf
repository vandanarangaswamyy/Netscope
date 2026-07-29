output "github_actions_role_arn" {
  description = "Set this value as the AWS_ROLE_ARN GitHub repository secret."
  value       = aws_iam_role.github_actions.arn
}

output "github_oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN."
  value       = local.oidc_provider_arn
}

output "trusted_github_subject_claim" {
  description = "Exact GitHub OIDC subject claim trusted by this role."
  value       = local.github_subject_claim
}
