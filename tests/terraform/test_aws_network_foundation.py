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
