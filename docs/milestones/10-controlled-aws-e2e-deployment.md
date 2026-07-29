# Milestone 10: Controlled End-To-End AWS Deployment Sequence

## Networking Concept

An end-to-end cloud reliability test should prove the full private path without leaving expensive or exposed resources behind. The test starts with image publishing, creates the private AWS environment, verifies service health behind the internal ALB, proves internal-only connectivity, captures CloudWatch and VPC Flow Log evidence, and destroys everything the same day.

This milestone prepares the procedure only. It does not create AWS resources.

## Proposed Folder Structure

```text
.
├── docs/milestones/10-controlled-aws-e2e-deployment.md
├── docs/runbooks/aws-end-to-end-deployment.md
├── ops/aws/evidence-log-template.md
└── tests/test_aws_e2e_runbook.py
```

## Implemented Feature

This milestone adds a controlled AWS runbook covering:

- ECR creation through Terraform.
- Docker image build and push to ECR.
- Linux/amd64 image build using Docker Buildx for Apple Silicon compatibility.
- Saved Terraform plan and apply sequence for private ECS deployment.
- ECS service stability checks.
- Internal ALB target health checks.
- Internal-only connectivity test from a private Fargate task.
- CloudWatch application log evidence.
- VPC Flow Log accepted/rejected traffic evidence.
- Cost safeguards.
- Same-day saved destroy plan and destroy sequence.
- State backup points before and after apply/destroy.
- Git ignore verification for Terraform state, saved plans, and backup paths.
- Explicit ECR image deletion before destroy so a non-empty repository cannot block cleanup.
- Post-destroy checks for empty Terraform state and absence of NetScope AWS resources.

## Cost Safeguards

The runbook keeps these defaults unless explicitly changed:

```hcl
enable_nat_gateway=false
enable_service_deployment=true
enable_private_image_pull_endpoints=true
enable_ecr_repository=true
```

Private image-pull endpoints have hourly costs, as do ECS Fargate tasks, ALB, VPC Flow Logs storage, and ECR storage. The runbook requires same-day destroy after evidence collection.

The first ECR apply currently creates the default network foundation too, including the internal ALB, so billable usage begins before ECS services are deployed.

## Automated Tests

Run:

```bash
uv run pytest
terraform -chdir=infra/terraform/aws fmt -check
terraform -chdir=infra/terraform/aws validate
```

The tests verify the runbook includes:

- ECR creation.
- Image build and push.
- Linux/amd64 Buildx usage.
- Saved Terraform plans.
- Private ECS apply.
- ECS stable wait.
- ALB target health verification.
- Internal Fargate smoke test.
- CloudWatch and Flow Log evidence capture.
- Cost safeguards and same-day destroy.
- ECR image cleanup before destroy.
- Smoke-test task ARN capture, non-empty ARN assertion, stopped-task wait, describe call, and enforced exit code `0`.
- ECR image deletion without ignored errors, followed by empty image-list verification.
- Explicit pre-destroy Terraform state backup.
- Post-destroy absence checks.

## Manual Verification

Review the runbook:

```bash
less docs/runbooks/aws-end-to-end-deployment.md
```

Dry-review the command sequence and variables. Do not run apply yet.

Expected review result:

- Every billable step is explicit.
- Terraform state is backed up before and after resource changes.
- Terraform state, saved plans, and backup paths are ignored by Git.
- Apply uses saved plan files.
- Destroy uses a saved destroy plan.
- Internal connectivity is tested from inside private subnets.

## Expected Result

After manual review, the project has a safe operator sequence for a short-lived AWS deployment test. No AWS infrastructure is created until you explicitly run the apply steps.
