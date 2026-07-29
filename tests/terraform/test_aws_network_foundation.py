from pathlib import Path


TERRAFORM_DIR = Path("infra/terraform/aws")


def read_tf(name: str) -> str:
    return (TERRAFORM_DIR / name).read_text()


def test_aws_network_foundation_declares_required_resources():
    main_tf = read_tf("main.tf")
    required_resources = [
        'resource "aws_vpc" "this"',
        'resource "aws_subnet" "public"',
        'resource "aws_subnet" "private"',
        'resource "aws_route_table" "public"',
        'resource "aws_route_table" "private"',
        'resource "aws_internet_gateway" "this"',
        'resource "aws_nat_gateway" "this"',
        'resource "aws_security_group" "internal_lb"',
        'resource "aws_security_group" "service_nodes"',
        'resource "aws_lb" "internal"',
        'resource "aws_lb_target_group" "service_nodes"',
        'resource "aws_lb_listener" "service"',
        'resource "aws_route53_zone" "private"',
        'resource "aws_route53_record" "service"',
        'resource "aws_flow_log" "vpc"',
        'resource "aws_cloudwatch_log_group" "vpc_flow_logs"',
        'resource "aws_iam_role" "vpc_flow_logs"',
    ]

    for resource in required_resources:
        assert resource in main_tf


def test_aws_network_foundation_uses_two_public_and_private_subnets():
    main_tf = read_tf("main.tf")

    assert 'resource "aws_subnet" "public"' in main_tf
    assert 'resource "aws_subnet" "private"' in main_tf
    assert "count = 2" in main_tf
    assert "data.aws_availability_zones.available.names[count.index]" in main_tf


def test_nat_gateway_is_disabled_by_default_for_cost_control():
    variables_tf = read_tf("variables.tf")
    main_tf = read_tf("main.tf")

    assert 'variable "enable_nat_gateway"' in variables_tf
    assert "default     = false" in variables_tf
    assert "count = var.enable_nat_gateway ? 1 : 0" in main_tf


def test_load_balancer_is_internal_and_nodes_are_private():
    main_tf = read_tf("main.tf")

    assert "internal           = true" in main_tf
    assert "subnets            = aws_subnet.private[*].id" in main_tf
    assert 'resource "aws_security_group_rule" "service_nodes_ingress_lb"' in main_tf
    assert "source_security_group_id = aws_security_group.internal_lb.id" in main_tf
    assert "map_public_ip_on_launch = false" in main_tf


def test_flow_logs_default_to_enabled_with_short_retention():
    variables_tf = read_tf("variables.tf")
    main_tf = read_tf("main.tf")

    assert 'variable "enable_flow_logs"' in variables_tf
    assert "default     = true" in variables_tf
    assert 'variable "flow_log_retention_days"' in variables_tf
    assert "default     = 7" in variables_tf
    assert 'traffic_type    = "ALL"' in main_tf


def test_ecs_service_deployment_is_opt_in_and_private():
    variables_tf = read_tf("variables.tf")
    ecs_tf = read_tf("ecs.tf")

    assert 'variable "enable_service_deployment"' in variables_tf
    assert "default     = false" in variables_tf
    assert 'resource "aws_ecs_cluster" "this"' in ecs_tf
    assert 'resource "aws_ecs_task_definition" "dbnode"' in ecs_tf
    assert 'resource "aws_ecs_service" "dbnode"' in ecs_tf
    assert 'subnets          = aws_subnet.private[*].id' in ecs_tf
    assert 'security_groups  = [aws_security_group.service_nodes.id]' in ecs_tf
    assert "assign_public_ip = false" in ecs_tf


def test_ecs_deploys_three_named_dbnode_services():
    ecs_tf = read_tf("ecs.tf")

    assert "node-a" in ecs_tf
    assert "node-b" in ecs_tf
    assert "node-c" in ecs_tf
    assert "desired_count   = 1" in ecs_tf
    assert "NODE_ID" in ecs_tf
    assert "SIMULATED_LATENCY_MS" in ecs_tf


def test_ecs_service_registers_with_internal_alb_target_group():
    ecs_tf = read_tf("ecs.tf")

    assert "target_group_arn = aws_lb_target_group.service_nodes.arn" in ecs_tf
    assert 'container_name   = "dbnode"' in ecs_tf
    assert "container_port   = var.node_port" in ecs_tf
    assert "aws_lb_listener.service" in ecs_tf


def test_ecs_logs_and_image_pull_controls_exist():
    variables_tf = read_tf("variables.tf")
    ecs_tf = read_tf("ecs.tf")

    assert 'resource "aws_cloudwatch_log_group" "dbnode"' in ecs_tf
    assert "awslogs-group" in ecs_tf
    assert 'variable "enable_private_image_pull_endpoints"' in variables_tf
    assert 'resource "aws_vpc_endpoint" "ecr_api"' in ecs_tf
    assert 'resource "aws_vpc_endpoint" "ecr_dkr"' in ecs_tf
    assert 'resource "aws_vpc_endpoint" "logs"' in ecs_tf
    assert 'resource "aws_vpc_endpoint" "s3"' in ecs_tf
