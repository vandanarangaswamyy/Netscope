# Milestone 9: Secure GitHub Actions OIDC Setup

## Networking Concept

CI/CD systems should use short-lived cloud credentials instead of static AWS access keys. GitHub Actions OIDC lets a workflow exchange a GitHub-issued identity token for AWS STS credentials, but only if AWS trusts that workflow identity.

The key control is the IAM role trust policy. It must restrict:

- the issuer to GitHub Actions OIDC,
- the audience to AWS STS,
- the subject to this repository and branch.

For NetScope, the default trusted subject is:

```text
repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main
```

## Proposed Folder Structure

```text
.
├── docs/milestones/09-github-oidc-setup.md
├── infra/terraform/github-oidc
│   ├── README.md
│   ├── main.tf
│   ├── outputs.tf
│   ├── variables.tf
│   └── versions.tf
└── tests/terraform/test_github_oidc_bootstrap.py
```

## Implemented Feature

This milestone adds a separate Terraform bootstrap stack for GitHub Actions AWS access:

- GitHub Actions IAM OIDC provider.
- IAM role for the NetScope workflow.
- Trust policy restricted to:
  - `token.actions.githubusercontent.com:aud = sts.amazonaws.com`
  - `token.actions.githubusercontent.com:sub = repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main`
- Wildcard rejection for the subject claim variable.
- Least-privilege IAM policy for:
  - Terraform plan read-only discovery.
  - Optional ECR image push to `netscope-dbnode`.
- Output for the `AWS_ROLE_ARN` GitHub secret.

## GitHub API Discovery

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

The Terraform trust policy computes this exact branch-scoped subject:

```text
repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main
```

It uses explicit validated variables:

```hcl
github_owner                = "vandanarangaswamyy"
github_owner_id             = "181282565"
github_repository           = "Netscope"
github_repository_id        = "1308859104"
github_branch               = "main"
github_subject_claim_prefix = "repo:vandanarangaswamyy@181282565/Netscope@1308859104"
```

Do not use repository or branch wildcards.

## Permissions Boundary

The role is intended for the manual `AWS Image And Terraform Plan` workflow.

Allowed:

- AWS read/list/describe actions needed by Terraform plan.
- ECR auth token retrieval.
- ECR image push actions scoped to the configured dbnode repository.

Not allowed:

- Terraform apply.
- Terraform destroy.
- Creating VPCs, load balancers, Route 53 zones, ECS services, or IAM roles from GitHub Actions.

## GitHub Secret Setup

Do not create secrets automatically. After manual Terraform apply, get the role ARN:

```bash
terraform -chdir=infra/terraform/github-oidc output github_actions_role_arn
```

Then add it in GitHub:

```text
Repository > Settings > Secrets and variables > Actions > New repository secret
Name: AWS_ROLE_ARN
Value: <github_actions_role_arn>
```

## Automated Tests

Run:

```bash
uv run pytest
terraform -chdir=infra/terraform/github-oidc fmt -check
terraform -chdir=infra/terraform/github-oidc validate
```

The tests verify:

- The OIDC provider, role, policy, and attachment exist.
- The trust policy includes audience and subject conditions.
- The default subject is restricted to `vandanarangaswamyy@181282565/Netscope@1308859104` on `main`.
- Subject and branch wildcards are rejected.
- Plan permissions are read-only except for scoped ECR push.
- Secret setup is documented.

## Manual Verification

Initialize:

```bash
terraform -chdir=infra/terraform/github-oidc init
```

Review the plan only:

```bash
terraform -chdir=infra/terraform/github-oidc plan
```

Do not run apply until you are ready to create the IAM provider and role.

## Verified Result

After correcting the trust subject to the GitHub API-confirmed value, the manual `AWS Image And Terraform Plan` workflow was rerun successfully:

- Tests completed successfully.
- Terraform plan completed successfully.
- `build-image` was correctly skipped with `push_image=false`.
- No infrastructure was applied.

The trusted subject used by AWS is:

```text
repo:vandanarangaswamyy@181282565/Netscope@1308859104:ref:refs/heads/main
```

## Expected Result

The plan should show IAM-only resources for GitHub Actions OIDC. No GitHub secrets are created automatically, and no workflow is run automatically.
