data "aws_caller_identity" "current" {}

locals {
  oidc_provider_host   = replace(var.github_oidc_provider_url, "https://", "")
  ecr_repository_arn   = "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.ecr_repository_name}"
  github_subject_claim = "${var.github_subject_claim_prefix}:ref:refs/heads/${var.github_branch}"
  oidc_provider_arn    = var.existing_github_oidc_provider_arn != "" ? var.existing_github_oidc_provider_arn : aws_iam_openid_connect_provider.github[0].arn
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.existing_github_oidc_provider_arn == "" ? 1 : 0

  url = var.github_oidc_provider_url

  client_id_list = [
    var.github_oidc_audience,
  ]
}

data "aws_iam_policy_document" "trust" {
  statement {
    sid     = "AllowGitHubActionsMainBranch"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:aud"
      values   = [var.github_oidc_audience]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_provider_host}:sub"
      values   = [local.github_subject_claim]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = var.role_name
  description        = "Least-privilege GitHub Actions role for Netscope Terraform plan and optional ECR image push."
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

data "aws_iam_policy_document" "github_actions" {
  statement {
    sid    = "AllowTerraformPlanReadOnly"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "elasticloadbalancing:Describe*",
      "route53:Get*",
      "route53:List*",
      "logs:Describe*",
      "logs:List*",
      "iam:Get*",
      "iam:List*",
      "ecs:Describe*",
      "ecs:List*",
      "ecr:Describe*",
      "ecr:List*",
      "ecr:GetLifecyclePolicy",
      "ecr:GetRepositoryPolicy",
      "ecr:GetAuthorizationToken",
      "sts:GetCallerIdentity",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "AllowDbnodeImagePush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:ListImages",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [local.ecr_repository_arn]
  }
}

resource "aws_iam_policy" "github_actions" {
  name        = "${var.role_name}-policy"
  description = "Permissions for Netscope GitHub Actions Terraform plan and optional ECR image push."
  policy      = data.aws_iam_policy_document.github_actions.json
}

resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions.arn
}
