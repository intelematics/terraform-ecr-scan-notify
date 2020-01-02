variable "slack_webhook_url" {
  type = string
}
variable "slack_channel" {
  type = string
}
variable "send_slack_message_if_no_findings" {
  type    = bool
  default = false
}
