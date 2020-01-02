# ECR Image Scan Notify

Terraform module to set up [ECR Image Scan Results](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_DescribeImageScanFindings.html) notifications from CloudWatch, invoke a lambda which sends these to slack.

# Usage

```terraform
module "ecr_scan_notify" {
  source                              = "git@github.com:intelematics/terraform-ecr-scan-notify.git"
  slack_webhook_url                   = var.slack_webhook_url
  slack_channel                       = var.slack_channel
  send_slack_message_if_no_findings   = true
}
```

# Requires

**Recent AWS Terraform Provider**

Version ~> 2.42.0

**ECR Scan on Push Configured**
https://www.terraform.io/docs/providers/aws/r/ecr_repository.html

```terraform
resource "aws_ecr_repository" "foo" {
  name                 = "bar"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
```

**Slack Incoming Webhook Configured**

To view Intelematics' incoming webhooks: https://intelematics.slack.com/apps/A0F7XDUAZ-incoming-webhooks?next_id=0

Request Configuration for your channel (requires an admin approval)

From there you'll get the Webhook URL

# Variables
|Name|Default
|-|
|slack_webhook_url
|slack_channel
|send_slack_message_if_no_findings|false

# Notes

At time of writing, I couldn't manually tell ECR to scan an image, received error "There was an error scanning the selected image"; the only way I could test was setting the repo "Scan on push" then pushing a new image.
