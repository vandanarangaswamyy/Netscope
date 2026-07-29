# Milestone 8: AWS Deployment Operations

## Networking Concept

Once private AWS networking and ECS service definitions exist, deployment operations need guardrails. Image publishing, Terraform planning, and AWS credentials should be repeatable without making destructive changes automatically.

This milestone adds a manual GitHub Actions workflow that can:

- Run the full test suite.
- Build and push the dbnode image to ECR.
- Run Terraform formatting, initialization, validation, and plan.

It intentionally does not run `terraform apply` or `terraform destroy` because the Terraform stack still uses local state. Applying from an ephemeral GitHub Actions runner without remote state could make later cleanup unsafe. Apply and destroy remain local operator actions until a remote backend milestone is added.

## Proposed Folder Structure

```text
.
├── .github/workflows/aws-plan.yml
├── docs/milestones/08-aws-deployment-operations.md
├── infra/terraform/aws
│   ├── ecr.tf
│   ├── outputs.tf
│   └── variables.tf
└── tests
    ├── test_github_actions_workflows.py
    └── terraform/test_aws_network_foundation.py
```

## Implemented Feature

This milestone adds:

- Optional Terraform-managed ECR repository:
  - `enable_ecr_repository`
  - `ecr_repository_name`
- ECR lifecycle policy that keeps the most recent 10 images.
- Manual GitHub Actions workflow: `AWS Image And Terraform Plan`.
- OIDC-based AWS authentication through `secrets.AWS_ROLE_ARN`.
- Optional image build and push.
- Terraform plan inputs for:
  - ECR repository creation.
  - ECS service deployment.
  - Private image-pull endpoints.
  - NAT gateway.
  - dbnode image URI.

## Required GitHub Secret

Configure this repository secret:

```text
AWS_ROLE_ARN
```

The role should trust GitHub OIDC for this repository and should have only the permissions needed for ECR image push and Terraform planning. Keep apply/destroy permissions out of this workflow role unless a future remote-state deployment workflow requires them.

## ECR Repository Workflow

Review Terraform-managed ECR repository creation:

```bash
terraform -chdir=infra/terraform/aws plan -var='enable_ecr_repository=true'
```

Apply locally only when you are ready:

```bash
terraform -chdir=infra/terraform/aws apply -var='enable_ecr_repository=true'
```

After the repository exists, run the GitHub workflow manually with:

```text
push_image=true
ecr_repository=netscope-dbnode
image_tag=<commit-sha-or-version>
```

## ECS Plan Workflow

To produce a private ECS deployment plan after pushing an image, run the workflow manually with:

```text
push_image=true
enable_service_deployment=true
enable_private_image_pull_endpoints=true
enable_nat_gateway=false
```

The workflow will build and push:

```text
ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/netscope-dbnode:<image_tag>
```

Then it will run Terraform plan with that image URI.

## Local Apply And Destroy

Apply remains local for now:

```bash
terraform -chdir=infra/terraform/aws apply \
  -var='enable_ecr_repository=true' \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:IMAGE_TAG'
```

Destroy with the same variable set:

```bash
terraform -chdir=infra/terraform/aws destroy \
  -var='enable_ecr_repository=true' \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='dbnode_image_uri=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/netscope-dbnode:IMAGE_TAG'
```

## Automated Tests

Run:

```bash
uv run pytest
terraform -chdir=infra/terraform/aws fmt -check
terraform -chdir=infra/terraform/aws validate
```

The tests verify:

- The AWS workflow is manual-only.
- The workflow uses GitHub OIDC.
- The workflow can build and push the dbnode image.
- The workflow runs Terraform plan only.
- Terraform-managed ECR is optional and scan-on-push is enabled.

## Manual Verification

From GitHub Actions, open:

```text
Actions > AWS Image And Terraform Plan > Run workflow
```

For a safe default validation, use:

```text
push_image=false
enable_ecr_repository=false
enable_service_deployment=false
enable_private_image_pull_endpoints=false
enable_nat_gateway=false
```

Expected result:

- Tests pass.
- Terraform fmt and validate pass.
- Terraform plan is generated.
- No apply or destroy runs.
