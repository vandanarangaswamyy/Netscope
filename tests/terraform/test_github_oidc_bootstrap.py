from pathlib import Path


OIDC_DIR = Path("infra/terraform/github-oidc")


def read_tf(name: str) -> str:
    return (OIDC_DIR / name).read_text()


def test_github_oidc_stack_declares_provider_role_and_policy():
    main_tf = read_tf("main.tf")
    variables_tf = read_tf("variables.tf")

    assert 'resource "aws_iam_openid_connect_provider" "github"' in main_tf
    assert 'resource "aws_iam_role" "github_actions"' in main_tf
    assert 'resource "aws_iam_policy" "github_actions"' in main_tf
    assert 'resource "aws_iam_role_policy_attachment" "github_actions"' in main_tf
    assert 'variable "existing_github_oidc_provider_arn"' in variables_tf
    assert "local.oidc_provider_arn" in main_tf


def test_github_oidc_trust_is_restricted_to_repo_main_and_audience():
    variables_tf = read_tf("variables.tf")
    main_tf = read_tf("main.tf")

    assert 'default     = "vandanarangaswamyy"' in variables_tf
    assert 'default     = "Netscope"' in variables_tf
    assert 'default     = "main"' in variables_tf
    assert 'default     = "repo:vandanarangaswamyy/Netscope:ref:refs/heads/main"' in variables_tf
    assert 'variable = "${local.oidc_provider_host}:aud"' in main_tf
    assert 'variable = "${local.oidc_provider_host}:sub"' in main_tf
    assert "var.github_subject_claim" in main_tf


def test_github_subject_claim_rejects_wildcards():
    variables_tf = read_tf("variables.tf")

    assert "!strcontains(var.github_subject_claim, \"*\")" in variables_tf
    assert "!strcontains(var.github_subject_claim, \"?\")" in variables_tf


def test_github_actions_policy_is_plan_only_except_ecr_push():
    main_tf = read_tf("main.tf")

    assert '"ec2:Describe*"' in main_tf
    assert '"elasticloadbalancing:Describe*"' in main_tf
    assert '"route53:List*"' in main_tf
    assert '"ecs:Describe*"' in main_tf
    assert '"ecr:PutImage"' in main_tf
    assert '"ecr:UploadLayerPart"' in main_tf
    assert "local.ecr_repository_arn" in main_tf

    forbidden_actions = [
        "ec2:CreateVpc",
        "ecs:CreateService",
        "iam:CreateRole",
        "route53:CreateHostedZone",
        "elasticloadbalancing:CreateLoadBalancer",
        "terraform apply",
        "terraform destroy",
    ]
    for action in forbidden_actions:
        assert action not in main_tf


def test_github_secret_setup_is_documented():
    readme = read_tf("README.md")
    outputs_tf = read_tf("outputs.tf")

    assert "AWS_ROLE_ARN" in readme
    assert "New repository secret" in readme
    assert 'output "github_actions_role_arn"' in outputs_tf
