# GitHub Actions OIDC Bootstrap

This Terraform stack creates the IAM setup that lets the NetScope GitHub Actions workflow request short-lived AWS credentials through OIDC.

It is separate from `infra/terraform/aws` so you can review and manage GitHub Actions access independently from the lab network and ECS resources.

## What It Creates

- IAM OIDC provider for `https://token.actions.githubusercontent.com`.
- IAM role for GitHub Actions.
- Trust policy restricted to:
  - audience: `sts.amazonaws.com`
  - subject: `repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main`
- Least-privilege policy for:
  - Terraform plan read-only discovery.
- Optional dbnode image push to one ECR repository.

If your AWS account already has a GitHub Actions OIDC provider, pass it instead of creating a duplicate:

```bash
terraform plan -var='existing_github_oidc_provider_arn=arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com'
```

## Important Subject Claim Note

GitHub documents repository OIDC customization through the Actions OIDC REST API. Use this command to discover the subject settings for NetScope:

```bash
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  /repos/vandanarangaswamyy/Netscope/actions/oidc/customization/sub
```

The confirmed response was:

```json
{
  "use_default": true,
  "use_immutable_subject": false,
  "sub_claim_prefix": "repo:vandanarangaswamyy@181282565/Netscope@1308859104"
}
```

The default subject claim is:

```text
repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main
```

It is computed from explicit validated variables:

```hcl
github_owner                = "vandanarangaswamyy"
github_owner_id             = "181282565"
github_repository           = "Netscope"
github_repository_id        = "1308859104"
github_branch               = "main"
github_subject_claim_prefix = "repo:vandanarangaswamyy@181282565/Netscope@1308859104"
```

Do not use repository or branch wildcards. Subject-related variables reject `*` and `?`, and the prefix must match the explicit owner and repository IDs.

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

## Verified Workflow Result

With `AWS_ROLE_ARN` configured and the subject claim corrected to the API-confirmed value, the manual `AWS Image And Terraform Plan` workflow completed successfully with `push_image=false`. Tests and Terraform plan passed, `build-image` was skipped, and no infrastructure was applied.
