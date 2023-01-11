variable "region" {
  default     = "us-central1"
  description = "Region where entite infra is to be provisioned preferably us-east-1 for Cloud function is supported in this region"
}
variable "gcp_project" {
  default     = "devops-casestudy-20200608"
  description = "GCP Project id"
}
variable "credentials" {
  default     = "devops-casestudy-org.json"
  description = "Service Account json file name"
}
variable "topic_name" {
  default     = "autotag-topic"
  description = "Name of Pubsub Topic"
}

variable "bucket_name" {
  default     = "autotag_test1235"
  description = "GCS Bucket details for cf code storage"
}

variable "function_name" {
  default     = "autotag_function"
  description = "Cloud function name"
}
variable "webhook" {
  description = "Slack Webhook URL"
}

variable "sa" {
  description = "Display name of service account of Cloud function"
  default = "disksa"
}
