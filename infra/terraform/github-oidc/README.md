# GitHub Actions OIDC Bootstrap

This Terraform stack creates the IAM setup that lets the NetScope GitHub Actions workflow request short-lived AWS credentials through OIDC.

It is separate from `infra/terraform/aws` so you can review and manage GitHub Actions access independently from the lab network and ECS resources.

## What It Creates

- IAM OIDC provider for `https://token.actions.githubusercontent.com`.
- IAM role for GitHub Actions.
- Trust policy restricted to:
  - audience: `sts.amazonaws.com`
  - subject: `repo:vandanarangaswamyy/Netscope:ref:refs/heads/main`
- Least-privilege policy for:
  - Terraform plan read-only discovery.
- Optional dbnode image push to one ECR repository.

If your AWS account already has a GitHub Actions OIDC provider, pass it instead of creating a duplicate:

```bash
terraform plan -var='existing_github_oidc_provider_arn=arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com'
```

## Important Subject Claim Note

GitHub documents that repositories created after July 15, 2026, or repositories that opt in to immutable subject claims, may use an immutable `sub` format with owner and repository IDs.

The default subject claim is:

```text
repo:vandanarangaswamyy/Netscope:ref:refs/heads/main
```

If GitHub shows an immutable claim for this repository, pass it explicitly:

```bash
terraform plan -var='github_subject_claim=repo:OWNER@OWNER_ID/REPO@REPO_ID:ref:refs/heads/main'
```

Do not use wildcards. The variable rejects `*` and `?`.

## Commands

Review formatting:

```bash
terraform -chdir=infra/terraform/github-oidc fmt -check
```

Initialize:

```bash
terraform -chdir=infra/terraform/github-oidc init
```

Review:

```bash
terraform -chdir=infra/terraform/github-oidc plan
```

Apply only after manual review:

```bash
terraform -chdir=infra/terraform/github-oidc apply
```

Get the role ARN:

```bash
terraform -chdir=infra/terraform/github-oidc output github_actions_role_arn
```

Destroy:

```bash
terraform -chdir=infra/terraform/github-oidc destroy
```

## GitHub Secret Setup

After applying the stack, add a repository secret:

```text
Name: AWS_ROLE_ARN
Value: <github_actions_role_arn output>
```

Do this manually in GitHub:

```text
Repository > Settings > Secrets and variables > Actions > New repository secret
```

The workflow will not work until this secret exists.

## Scope Boundary

This role is intentionally not an apply role. It has read-only permissions for Terraform plans and write permissions only for pushing images to the configured ECR repository.

The workflow remains manual-only and does not run `terraform apply` or `terraform destroy`.
