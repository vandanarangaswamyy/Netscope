from pathlib import Path


RUNBOOK = Path("docs/runbooks/aws-end-to-end-deployment.md")
MILESTONE = Path("docs/milestones/10-controlled-aws-e2e-deployment.md")
EVIDENCE = Path("ops/aws/evidence-log-template.md")


def test_e2e_runbook_covers_required_deployment_phases():
    text = RUNBOOK.read_text()
    required = [
        "Phase 1: Preflight",
        "Phase 2: Create ECR",
        "Phase 3: Build And Push Image",
        "Phase 4: Apply Private AWS Infrastructure And ECS",
        "Phase 5: ECS And ALB Health Verification",
        "Phase 6: Internal Connectivity Test",
        "Phase 7: CloudWatch And Flow Log Evidence",
        "Phase 8: Same-Day Destroy",
    ]

    for item in required:
        assert item in text


def test_e2e_runbook_requires_saved_plans_and_state_backups():
    text = RUNBOOK.read_text()
    gitignore = Path(".gitignore").read_text()

    assert "-out=\"${PWD}/${BACKUP_DIR}/01-ecr.tfplan\"" in text
    assert "-out=\"${PWD}/${BACKUP_DIR}/02-private-ecs.tfplan\"" in text
    assert "-out=\"${PWD}/${BACKUP_DIR}/03-destroy.tfplan\"" in text
    assert "terraform.tfstate.pre-e2e.bak" in text
    assert "terraform.tfstate.after-ecr.bak" in text
    assert "terraform.tfstate.after-ecs.bak" in text
    assert "terraform.tfstate.after-destroy.bak" in text
    assert "git check-ignore" in text
    assert "*.tfstate" in gitignore
    assert "*.tfplan" in gitignore
    assert ".terraform-state-backups/" in gitignore


def test_e2e_runbook_runs_init_before_validate():
    text = RUNBOOK.read_text()

    init_index = text.index('terraform -chdir="${TF_DIR}" init')
    validate_index = text.index('terraform -chdir="${TF_DIR}" validate')
    assert init_index < validate_index


def test_e2e_runbook_keeps_nat_disabled_and_tasks_private():
    text = RUNBOOK.read_text()

    assert "-var='enable_nat_gateway=false'" in text
    assert "assignPublicIp=DISABLED" in text
    assert "assign_public_ip = true" in text
    assert "ALB is not internal" in text


def test_e2e_runbook_verifies_ecs_alb_internal_connectivity_and_logs():
    text = RUNBOOK.read_text()

    assert "aws ecs wait services-stable" in text
    assert "aws elbv2 describe-target-health" in text
    assert "aws ecs run-task" in text
    assert "SMOKE_TASK_ARN" in text
    assert 'test -n "${SMOKE_TASK_ARN}"' in text
    assert 'test "${SMOKE_TASK_ARN}" != "None"' in text
    assert "aws ecs wait tasks-stopped" in text
    assert "aws ecs describe-tasks" in text
    assert "exitCode" in text
    assert ')\" = \"0\"' in text
    assert "analytics.netscope.local" in text or "${SERVICE_FQDN}" in text
    assert "aws logs filter-log-events" in text
    assert "--filter-pattern ACCEPT" in text
    assert "--filter-pattern REJECT" in text


def test_e2e_runbook_builds_linux_amd64_and_handles_ecr_cleanup():
    text = RUNBOOK.read_text()

    assert "docker buildx build" in text
    assert "--platform linux/amd64" in text
    assert "--push" in text
    assert "enabling ECR is not isolated" in text
    assert "internal ALB" in text
    assert "aws ecr batch-delete-image" in text
    assert "|| true" not in text
    assert "aws ecr list-images" in text
    assert "length(imageIds)" in text
    assert "non-empty repository cannot block cleanup" in text


def test_e2e_runbook_has_comprehensive_post_destroy_checks():
    text = RUNBOOK.read_text()

    assert 'terraform -chdir="${TF_DIR}" state list' in text
    assert "aws ecs describe-clusters" in text
    assert "aws elbv2 describe-load-balancers" in text
    assert "aws ec2 describe-vpc-endpoints" in text
    assert "aws ec2 describe-vpcs" in text
    assert "aws ecr describe-repositories" in text
    assert "aws route53 list-hosted-zones-by-name" in text
    assert "aws logs describe-log-groups" in text
    assert "terraform.tfstate.pre-destroy.bak" in text


def test_milestone_and_evidence_docs_exist_with_cost_cleanup_language():
    milestone = MILESTONE.read_text()
    evidence = EVIDENCE.read_text()

    assert "This milestone prepares the procedure only. It does not create AWS resources." in milestone
    assert "same-day destroy" in milestone
    assert "NAT gateway enabled: expected false" in evidence
    assert "Build platform: expected linux/amd64" in evidence
    assert "Smoke task ARN nonempty and not None" in evidence
    assert "Smoke task container exit code: expected 0" in evidence
    assert "ECR image list after deletion: expected empty" in evidence
    assert "Pre-destroy state backup path" in evidence
    assert "Post-destroy state backup path" in evidence
