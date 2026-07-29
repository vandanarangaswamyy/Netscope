# AWS End-To-End Deployment Runbook

This runbook is the controlled sequence for one same-day AWS deployment test of NetScope.

It creates billable resources only when you explicitly run the `terraform apply` commands. Do not run this sequence unless you are ready to create and destroy AWS resources on the same day.

## Ground Rules

- Use the `dev` AWS profile unless you intentionally choose another profile.
- Run `terraform init` before `terraform validate`.
- Save every Terraform plan with `-out`.
- Apply only the saved plan file.
- Back up Terraform state immediately before and after every apply or destroy.
- Back up Terraform state, plan files, and evidence locally, but never commit them.
- Keep NAT disabled unless you explicitly need it.
- Prefer private ECR, CloudWatch Logs, and S3 endpoints over NAT for this lab run.
- Destroy all resources the same day.
- Do not run apply or destroy from GitHub Actions; the workflow is plan-only until remote state is introduced.

## Variables

Set these shell variables before starting:

```bash
export AWS_PROFILE=dev
export AWS_REGION=us-east-1
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export IMAGE_TAG="$(git rev-parse --short HEAD)"
export ECR_REPOSITORY="netscope-dbnode"
export IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
export TF_DIR="infra/terraform/aws"
export BACKUP_DIR=".terraform-state-backups/aws-e2e-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"
```

Record the values in [ops/aws/evidence-log-template.md](../../ops/aws/evidence-log-template.md).

## Phase 1: Preflight

Confirm local validation:

```bash
uv run pytest
terraform -chdir="${TF_DIR}" fmt -check
terraform -chdir="${TF_DIR}" init
terraform -chdir="${TF_DIR}" validate
```

Verify Terraform state, saved plans, and backup paths are ignored by Git:

```bash
git check-ignore "${TF_DIR}/terraform.tfstate"
git check-ignore "${BACKUP_DIR}/terraform.tfstate.pre-e2e.bak"
git check-ignore "${BACKUP_DIR}/01-ecr.tfplan"
```

Confirm AWS identity:

```bash
aws sts get-caller-identity
```

Capture current state if it exists:

```bash
if [ -f "${TF_DIR}/terraform.tfstate" ]; then
  cp "${TF_DIR}/terraform.tfstate" "${BACKUP_DIR}/terraform.tfstate.pre-e2e.bak"
fi
```

## Phase 2: Create ECR And Network Foundation

Create a saved plan for the Terraform-managed ECR repository.

Important: with the current Terraform stack, enabling ECR is not isolated. This plan also creates the default AWS network foundation, including the internal ALB. Billable ALB, CloudWatch, VPC Flow Log, ECR, and related resource usage begins after apply. Review the full plan before continuing.

```bash
terraform -chdir="${TF_DIR}" plan \
  -var="aws_region=${AWS_REGION}" \
  -var='enable_ecr_repository=true' \
  -out="${PWD}/${BACKUP_DIR}/01-ecr.tfplan"
```

Review the plan. Expected intent:

```text
Create ECR repository netscope-dbnode, lifecycle policy, and the default network foundation including internal ALB and flow logs.
```

Apply only the saved plan:

```bash
terraform -chdir="${TF_DIR}" apply "${PWD}/${BACKUP_DIR}/01-ecr.tfplan"
```

Back up state immediately:

```bash
cp "${TF_DIR}/terraform.tfstate" "${BACKUP_DIR}/terraform.tfstate.after-ecr.bak"
```

## Phase 3: Build And Push Image

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
```

Build and push the dbnode image explicitly for `linux/amd64`. This matters when running from Apple Silicon:

```bash
docker buildx create --name netscope-builder --use || docker buildx use netscope-builder
docker buildx build \
  --platform linux/amd64 \
  -f services/dbnode/Dockerfile \
  -t "${IMAGE_URI}" \
  --push \
  .
```

Verify image availability:

```bash
aws ecr describe-images \
  --repository-name "${ECR_REPOSITORY}" \
  --image-ids imageTag="${IMAGE_TAG}"
```

## Phase 4: Apply Private AWS Infrastructure And ECS

Create a saved plan for the full private deployment:

```bash
terraform -chdir="${TF_DIR}" plan \
  -var="aws_region=${AWS_REGION}" \
  -var='enable_ecr_repository=true' \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='enable_nat_gateway=false' \
  -var="dbnode_image_uri=${IMAGE_URI}" \
  -out="${PWD}/${BACKUP_DIR}/02-private-ecs.tfplan"
```

Review the plan. Expected intent:

```text
Create private endpoints, ECS cluster, execution IAM, CloudWatch logs, and three private Fargate dbnode services.
```

Apply only the saved plan:

```bash
terraform -chdir="${TF_DIR}" apply "${PWD}/${BACKUP_DIR}/02-private-ecs.tfplan"
```

Back up state immediately:

```bash
cp "${TF_DIR}/terraform.tfstate" "${BACKUP_DIR}/terraform.tfstate.after-ecs.bak"
```

## Phase 5: ECS And ALB Health Verification

Capture Terraform outputs:

```bash
terraform -chdir="${TF_DIR}" output
terraform -chdir="${TF_DIR}" output -raw service_target_group_arn
terraform -chdir="${TF_DIR}" output -raw private_service_fqdn
```

Wait for ECS services to stabilize:

```bash
aws ecs wait services-stable \
  --cluster netscope-lab-cluster \
  --services netscope-lab-node-a netscope-lab-node-b netscope-lab-node-c
```

Describe ECS services:

```bash
aws ecs describe-services \
  --cluster netscope-lab-cluster \
  --services netscope-lab-node-a netscope-lab-node-b netscope-lab-node-c
```

Check ALB target health:

```bash
export TARGET_GROUP_ARN="$(terraform -chdir="${TF_DIR}" output -raw service_target_group_arn)"
aws elbv2 describe-target-health --target-group-arn "${TARGET_GROUP_ARN}"
```

Expected:

```text
Three healthy targets registered to the internal target group.
```

## Phase 6: Internal Connectivity Test

The ALB is internal, so test it from inside the VPC using a one-off Fargate task. This task reuses the dbnode image and overrides the command with a Python stdlib HTTP request.

Get private subnet and service security group IDs:

```bash
export PRIVATE_SUBNETS="$(terraform -chdir="${TF_DIR}" output -json private_subnet_ids)"
export SERVICE_SG="$(terraform -chdir="${TF_DIR}" output -raw service_node_security_group_id)"
export SERVICE_FQDN="$(terraform -chdir="${TF_DIR}" output -raw private_service_fqdn)"
```

Run one private smoke-test task and capture its task ARN:

```bash
export SMOKE_TASK_ARN="$(
  aws ecs run-task \
    --cluster netscope-lab-cluster \
    --launch-type FARGATE \
    --task-definition netscope-lab-node-a \
    --network-configuration "awsvpcConfiguration={subnets=${PRIVATE_SUBNETS},securityGroups=[${SERVICE_SG}],assignPublicIp=DISABLED}" \
    --overrides "{\"containerOverrides\":[{\"name\":\"dbnode\",\"command\":[\"python\",\"-c\",\"import urllib.request; print(urllib.request.urlopen('http://${SERVICE_FQDN}:8080/health', timeout=10).read().decode())\"]}]}" \
    --query 'tasks[0].taskArn' \
    --output text
)"
echo "${SMOKE_TASK_ARN}"
test -n "${SMOKE_TASK_ARN}"
test "${SMOKE_TASK_ARN}" != "None"
```

Wait for the one-off task to stop:

```bash
aws ecs wait tasks-stopped \
  --cluster netscope-lab-cluster \
  --tasks "${SMOKE_TASK_ARN}"
```

Describe the stopped task and require container exit code `0`:

```bash
aws ecs describe-tasks \
  --cluster netscope-lab-cluster \
  --tasks "${SMOKE_TASK_ARN}"

aws ecs describe-tasks \
  --cluster netscope-lab-cluster \
  --tasks "${SMOKE_TASK_ARN}" \
  --query 'tasks[0].containers[?name==`dbnode`].exitCode | [0]' \
  --output text

test "$(
  aws ecs describe-tasks \
    --cluster netscope-lab-cluster \
    --tasks "${SMOKE_TASK_ARN}" \
    --query 'tasks[0].containers[?name==`dbnode`].exitCode | [0]' \
    --output text
)" = "0"
```

Expected:

```text
The task starts in a private subnet, stops successfully, and the dbnode container exit code is 0.
```

## Phase 7: CloudWatch And Flow Log Evidence

Capture dbnode application logs:

```bash
aws logs filter-log-events \
  --log-group-name /aws/ecs/netscope-lab/dbnode \
  --limit 25
```

Capture VPC Flow Log accepted traffic:

```bash
aws logs filter-log-events \
  --log-group-name /aws/vpc/netscope-lab/flow-logs \
  --filter-pattern ACCEPT \
  --limit 25
```

Capture rejected traffic evidence, even if empty:

```bash
aws logs filter-log-events \
  --log-group-name /aws/vpc/netscope-lab/flow-logs \
  --filter-pattern REJECT \
  --limit 25
```

Record command output summaries in [ops/aws/evidence-log-template.md](../../ops/aws/evidence-log-template.md).

## Phase 8: Same-Day Destroy

Delete pushed ECR images before destroy so a non-empty repository cannot block cleanup:

```bash
aws ecr batch-delete-image \
  --repository-name "${ECR_REPOSITORY}" \
  --image-ids imageTag="${IMAGE_TAG}"

test "$(aws ecr list-images \
  --repository-name "${ECR_REPOSITORY}" \
  --query 'length(imageIds)' \
  --output text)" = "0"
```

Create an explicit pre-destroy state backup:

```bash
cp "${TF_DIR}/terraform.tfstate" "${BACKUP_DIR}/terraform.tfstate.pre-destroy.bak"
```

Create a saved destroy plan using the same variables:

```bash
terraform -chdir="${TF_DIR}" plan -destroy \
  -var="aws_region=${AWS_REGION}" \
  -var='enable_ecr_repository=true' \
  -var='enable_service_deployment=true' \
  -var='enable_private_image_pull_endpoints=true' \
  -var='enable_nat_gateway=false' \
  -var="dbnode_image_uri=${IMAGE_URI}" \
  -out="${PWD}/${BACKUP_DIR}/03-destroy.tfplan"
```

Review the destroy plan. Expected intent:

```text
Destroy all Terraform-managed ECR, VPC, endpoint, ALB, ECS, Route 53, CloudWatch, IAM execution-role, and Flow Log resources.
```

Apply only the saved destroy plan:

```bash
terraform -chdir="${TF_DIR}" apply "${PWD}/${BACKUP_DIR}/03-destroy.tfplan"
```

Back up final state:

```bash
cp "${TF_DIR}/terraform.tfstate" "${BACKUP_DIR}/terraform.tfstate.after-destroy.bak"
```

Verify Terraform state is empty:

```bash
terraform -chdir="${TF_DIR}" state list
```

Expected:

```text
No resources listed.
```

Run comprehensive AWS absence checks:

```bash
aws ecs describe-clusters \
  --clusters netscope-lab-cluster \
  --query 'clusters[?status!=`INACTIVE`]'

aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?starts_with(LoadBalancerName, `netscope-lab`)]'

aws ec2 describe-vpc-endpoints \
  --filters Name=tag:Project,Values=netscope \
  --query 'VpcEndpoints[]'

aws ec2 describe-vpcs \
  --filters Name=tag:Project,Values=netscope \
  --query 'Vpcs[]'

test "$(
  aws ecr describe-repositories \
    --repository-names "${ECR_REPOSITORY}" \
    --query 'length(repositories)' \
    --output text 2>/dev/null || echo 0
)" = "0"

aws route53 list-hosted-zones-by-name \
  --dns-name netscope.local \
  --query 'HostedZones[?Name==`netscope.local.`]'

aws logs describe-log-groups \
  --log-group-name-prefix /aws/ecs/netscope-lab

aws logs describe-log-groups \
  --log-group-name-prefix /aws/vpc/netscope-lab
```

Expected:

```text
No active NetScope ECS clusters, ALBs, VPC endpoints, VPCs, ECR repositories, private Route 53 zones, or CloudWatch log groups remain.
```

## Stop Conditions

Stop and do not apply if any of these are true:

- The plan enables `enable_nat_gateway=true` unexpectedly.
- Any service task has `assign_public_ip = true`.
- The ALB is not internal.
- Terraform state is missing and you cannot confirm whether resources already exist.
- Terraform state, plan files, or backup paths are not ignored by Git.
- You cannot back up the Terraform state file before creating resources.
- The destroy plan does not include all resources created during the run.
- The ECR repository still contains images and `terraform destroy` is blocked.
