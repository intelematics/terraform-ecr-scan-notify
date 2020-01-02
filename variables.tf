variable "slack_webhook_url" {}
variable "slack_channel" {}
variable "notify_no_vulnerabilities" {
  description = "Set to 'true' for slack messages when no vulnerabilities are found"
  default = "false"
}
