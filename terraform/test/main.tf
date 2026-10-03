provider "kubernetes" {
  config_path    = pathexpand(var.kubeconfig_path)
  config_context = var.kube_context
}

locals {
  manifest_files = toset([
    "app-configmap.yaml",
    "app-deployment.yaml",
    "app-service.yaml",
    "network-policy.yaml",
    "redis-service.yaml",
    "redis-statefulset.yaml",
  ])

  manifests = {
    for filename in local.manifest_files :
    trimsuffix(filename, ".yaml") => yamldecode(
      file("${path.module}/../../k8s/${filename}")
    )
  }
}

resource "kubernetes_namespace_v1" "test" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of"    = "devops-notes-lab"
      "app.kubernetes.io/managed-by" = "terraform"
      environment                    = "test"
    }
  }
}

resource "kubernetes_resource_quota_v1" "test" {
  metadata {
    name      = "test-quota"
    namespace = kubernetes_namespace_v1.test.metadata[0].name
  }

  spec {
    hard = {
      pods                   = "10"
      "requests.cpu"         = "1"
      "requests.memory"      = "1Gi"
      "requests.storage"     = "2Gi"
      "limits.cpu"           = "2"
      "limits.memory"        = "2Gi"
      persistentvolumeclaims = "2"
    }
  }
}

resource "kubernetes_limit_range_v1" "test" {
  metadata {
    name      = "container-defaults"
    namespace = kubernetes_namespace_v1.test.metadata[0].name
  }

  spec {
    limit {
      type = "Container"
      default = {
        cpu    = "500m"
        memory = "256Mi"
      }
      default_request = {
        cpu    = "100m"
        memory = "128Mi"
      }
    }
  }
}

resource "kubernetes_manifest" "workloads" {
  for_each = local.manifests

  manifest = merge(each.value, {
    metadata = merge(each.value.metadata, {
      namespace = var.namespace
    })
  })

  depends_on = [
    kubernetes_limit_range_v1.test,
    kubernetes_resource_quota_v1.test,
  ]
}
