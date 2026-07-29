from pathlib import Path


def read_workflow(name: str) -> str:
    return Path(".github/workflows", name).read_text()


def test_aws_plan_workflow_is_manual_only():
    workflow = read_workflow("aws-plan.yml")

    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "pull_request:" not in workflow


def test_aws_plan_workflow_uses_oidc_and_manual_inputs():
    workflow = read_workflow("aws-plan.yml")

    assert "id-token: write" in workflow
    assert "role-to-assume: ${{ secrets.AWS_ROLE_ARN }}" in workflow
    assert "enable_service_deployment:" in workflow
    assert "enable_nat_gateway:" in workflow
    assert "enable_private_image_pull_endpoints:" in workflow
    assert "push_image:" in workflow
    assert "aws-actions/configure-aws-credentials@v4" in workflow


def test_aws_plan_workflow_builds_image_and_runs_plan_only():
    workflow = read_workflow("aws-plan.yml")

    assert "docker build -f services/dbnode/Dockerfile" in workflow
    assert "docker push" in workflow
    assert "terraform -chdir=\"${TERRAFORM_DIR}\" plan" in workflow
    assert "terraform apply" not in workflow
    assert "terraform destroy" not in workflow
