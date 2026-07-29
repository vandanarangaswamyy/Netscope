resource "aws_ecr_repository" "dbnode" {
  count = var.enable_ecr_repository ? 1 : 0

  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${local.name_prefix}-dbnode-ecr"
  }
}

resource "aws_ecr_lifecycle_policy" "dbnode" {
  count = var.enable_ecr_repository ? 1 : 0

  repository = aws_ecr_repository.dbnode[0].name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep the most recent 10 dbnode images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
