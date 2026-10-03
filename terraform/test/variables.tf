variable "kubeconfig_path" {
  description = "Path to the kubeconfig file used for the test cluster."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Optional kubeconfig context for the test cluster."
  type        = string
  default     = null
  nullable    = true
}

variable "namespace" {
  description = "Namespace dedicated to the test environment."
  type        = string
  default     = "devops-notes-lab-test"

  validation {
    condition     = can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", var.namespace))
    error_message = "The namespace must be a valid Kubernetes DNS label."
  }
}
