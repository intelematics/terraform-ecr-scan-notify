locals {
  function_name                    = "ecr_scan_notify"
  permissions_boundary_policy_name = "managed-permission-boundary"
  ssm_parameter_name_config        = "ecr_scan_notify_config"
}

data "aws_caller_identity" "current" {}

module "ecr_scan_notify_lambda" {
  source = "github.com/intelematics/terraform-aws-lambda"

  # Where the lambda code lives
  source_path = "${path.module}/lambda/"

  function_name = "${local.function_name}"
  description   = "Notify via Slack of ECR Image Scan Results"
  handler       = "${local.function_name}.lambda_handler"
  runtime       = "python3.8"
  timeout       = 300 # 5 mins
  memory_size   = 256

  permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.permissions_boundary_policy_name}"

  # Attach a policy.
  policy = {
    json = data.aws_iam_policy_document.lambda.json
  }

  # Add a dead letter queue.
  dead_letter_config = {
    target_arn = aws_sqs_queue.dlq.arn
  }

  # Add environment variables.
  environment = {
    variables = {
      SSM_PARAMETER_NAME_CONFIG = local.ssm_parameter_name_config
    }
  }
}

resource "aws_ssm_parameter" "config" {
  name = local.ssm_parameter_name_config
  type = "SecureString"
  value = jsonencode({
    "slack_channel"     = "${var.slack_channel}",
    "slack_webhook_url" = "${var.slack_webhook_url}",
  })
}

resource "aws_sqs_queue" "dlq" {
  name = "${local.function_name}_dlq"
}

# The lambda only needs organizations:DescribeOrganization (and not iam:ListRoles)
# After that, it assumes roles (first in the Master, then in Members)
# in order to ListRoles
data "aws_iam_policy_document" "lambda" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:DescribeImageScanFindings",
    ]
    resources = ["*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
    ]
    resources = [aws_sqs_queue.dlq.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
    ]
    resources = [aws_ssm_parameter.config.arn]
  }
}
