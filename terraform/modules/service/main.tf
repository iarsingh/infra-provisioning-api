terraform {
  required_version = ">= 1.5.0"
}

variable "name" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,28}[a-z0-9]$", var.name))
    error_message = "name must be 3 to 30 lowercase letters, digits, or dashes."
  }
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging"], var.environment)
    error_message = "prod is not rendered by this module."
  }
}

variable "region" {
  type    = string
  default = "us-central1"
  validation {
    condition     = contains(["us-central1", "europe-west1", "asia-south1"], var.region)
    error_message = "region is not on the allowed list."
  }
}

variable "machine_type" {
  type    = string
  default = "e2-small"
  validation {
    condition     = contains(["e2-small", "e2-standard-2", "e2-standard-4"], var.machine_type)
    error_message = "machine_type must be one of the three sizes."
  }
}

variable "labels" {
  type = map(string)
  validation {
    condition     = contains(keys(var.labels), "team") && contains(keys(var.labels), "cost_center")
    error_message = "labels need team and cost_center."
  }
}

output "label" {
  value = "${var.name}-${var.environment}"
}

output "plan_summary" {
  value = {
    name         = var.name
    environment  = var.environment
    region       = var.region
    machine_type = var.machine_type
    labels       = var.labels
  }
}
