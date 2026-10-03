terraform {
  required_version = ">= 1.5.0"
}

variable "name" {
  type = string
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging"], var.environment)
    error_message = "prod is not rendered by this module."
  }
}

output "label" {
  value = "${var.name}-${var.environment}"
}
