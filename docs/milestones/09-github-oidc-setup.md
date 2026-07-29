# Milestone 9: Secure GitHub Actions OIDC Setup

## Networking Concept

CI/CD systems should use short-lived cloud credentials instead of static AWS access keys. GitHub Actions OIDC lets a workflow exchange a GitHub-issued identity token for AWS STS credentials, but only if AWS trusts that workflow identity.

The key control is the IAM role trust policy. It must restrict:

- the issuer to GitHub Actions OIDC,
- the audience to AWS STS,
- the subject to this repository and branch.

For NetScope, the default trusted subject is:

```text
repo:vandanarangaswamyy/Netscope:ref:refs/heads/main
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
  - `token.actions.githubusercontent.com:sub = repo:vandanarangaswamyy/Netscope:ref:refs/heads/main`
- Wildcard rejection for the subject claim variable.
- Least-privilege IAM policy for:
  - Terraform plan read-only discovery.
  - Optional ECR image push to `netscope-dbnode`.
- Output for the `AWS_ROLE_ARN` GitHub secret.

## Important GitHub Subject Claim Note

GitHub documents that repositories created after July 15, 2026, or repositories that opt in to immutable subject claims, may use immutable owner and repository IDs in the OIDC `sub` claim.

The default value is owner/name based:

```text
repo:vandanarangaswamyy/Netscope:ref:refs/heads/main
```

If GitHub shows an immutable claim for this repository, override it exactly:

```bash
terraform -chdir=infra/terraform/github-oidc plan \
  -var='github_subject_claim=repo:OWNER@OWNER_ID/REPO@REPO_ID:ref:refs/heads/main'
```

Do not use wildcards.

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
- The default subject is restricted to `vandanarangaswamyy/Netscope` on `main`.
- Subject wildcards are rejected.
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

## Expected Result

The plan should show IAM-only resources for GitHub Actions OIDC. No GitHub secrets are created automatically, and no workflow is run automatically.
