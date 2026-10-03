output "namespace" {
  description = "Namespace created for the test environment."
  value       = kubernetes_namespace_v1.test.metadata[0].name
}

output "application_service" {
  description = "Cluster-local service address of the application."
  value       = "app.${kubernetes_namespace_v1.test.metadata[0].name}.svc.cluster.local:8000"
}

output "port_forward_command" {
  description = "Command for opening the test application locally."
  value       = "kubectl -n ${kubernetes_namespace_v1.test.metadata[0].name} port-forward service/app 8084:8000"
}
