locals {
  ecs_nodes = {
    node-a = {
      simulated_latency_ms = 15
    }
    node-b = {
      simulated_latency_ms = 25
    }
    node-c = {
      simulated_latency_ms = 35
    }
  }
}

resource "terraform_data" "validate_dbnode_image" {
  count = var.enable_service_deployment ? 1 : 0

  input = var.dbnode_image_uri

  lifecycle {
    precondition {
      condition     = var.dbnode_image_uri != ""
      error_message = "dbnode_image_uri is required when enable_service_deployment is true."
    }
  }
}

resource "aws_cloudwatch_log_group" "dbnode" {
  count = var.enable_service_deployment ? 1 : 0

  name              = "/aws/ecs/${local.name_prefix}/dbnode"
  retention_in_days = 7
}

resource "aws_iam_role" "ecs_task_execution" {
  count = var.enable_service_deployment ? 1 : 0

  name = "${local.name_prefix}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  count = var.enable_service_deployment ? 1 : 0

  role       = aws_iam_role.ecs_task_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_cluster" "this" {
  count = var.enable_service_deployment ? 1 : 0

  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_task_definition" "dbnode" {
  for_each = var.enable_service_deployment ? local.ecs_nodes : {}

  family                   = "${local.name_prefix}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.service_task_cpu
  memory                   = var.service_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution[0].arn

  container_definitions = jsonencode([
    {
      name      = "dbnode"
      image     = var.dbnode_image_uri
      essential = true

      portMappings = [
        {
          containerPort = var.node_port
          hostPort      = var.node_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NODE_ID"
          value = each.key
        },
        {
          name  = "NODE_ROLE"
          value = "analytics-worker"
        },
        {
          name  = "SIMULATED_LATENCY_MS"
          value = tostring(each.value.simulated_latency_ms)
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.dbnode[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = each.key
        }
      }
    }
  ])

  depends_on = [terraform_data.validate_dbnode_image]
}

resource "aws_ecs_service" "dbnode" {
  for_each = var.enable_service_deployment ? local.ecs_nodes : {}

  name            = "${local.name_prefix}-${each.key}"
  cluster         = aws_ecs_cluster.this[0].id
  task_definition = aws_ecs_task_definition.dbnode[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
  enable_execute_command             = false

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.service_nodes.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.service_nodes.arn
    container_name   = "dbnode"
    container_port   = var.node_port
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution,
    aws_lb_listener.service
  ]
}

resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  name        = "${local.name_prefix}-vpc-endpoints-sg"
  description = "Allow private ECS tasks to reach image pull and log endpoints."
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-vpc-endpoints-sg"
  }
}

resource "aws_security_group_rule" "vpc_endpoints_ingress_nodes" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  type                     = "ingress"
  description              = "Private nodes to interface endpoints"
  security_group_id        = aws_security_group.vpc_endpoints[0].id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.service_nodes.id
}

resource "aws_vpc_endpoint" "ecr_api" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-ecr-api-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-ecr-dkr-endpoint"
  }
}

resource "aws_vpc_endpoint" "logs" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-logs-endpoint"
  }
}

resource "aws_vpc_endpoint" "s3" {
  count = var.enable_private_image_pull_endpoints ? 1 : 0

  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]

  tags = {
    Name = "${local.name_prefix}-s3-endpoint"
  }
}
