import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
K8S_DIR = PROJECT_ROOT / "k8s"


class KubernetesConfigTestCase(unittest.TestCase):
    def test_kustomization_contains_every_manifest(self):
        kustomization = (K8S_DIR / "kustomization.yaml").read_text(encoding="utf-8")
        expected = {
            "namespace.yaml",
            "app-configmap.yaml",
            "app-deployment.yaml",
            "app-service.yaml",
            "redis-service.yaml",
            "redis-statefulset.yaml",
            "network-policy.yaml",
        }

        for manifest in expected:
            with self.subTest(manifest=manifest):
                self.assertTrue((K8S_DIR / manifest).is_file())
                self.assertIn(f"- {manifest}", kustomization)

        self.assertIn("namespace: devops-notes-lab", kustomization)

    def test_application_deployment_has_probes_resources_and_hardening(self):
        deployment = (K8S_DIR / "app-deployment.yaml").read_text(encoding="utf-8")

        self.assertIn("replicas: 2", deployment)
        self.assertIn("path: /health", deployment)
        self.assertIn("path: /ready", deployment)
        self.assertIn("requests:", deployment)
        self.assertIn("limits:", deployment)
        self.assertIn("runAsNonRoot: true", deployment)
        self.assertIn("readOnlyRootFilesystem: true", deployment)
        self.assertIn("allowPrivilegeEscalation: false", deployment)
        self.assertIn("type: RuntimeDefault", deployment)
        self.assertIn("- ALL", deployment)

    def test_application_image_and_config_use_project_version(self):
        version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        deployment = (K8S_DIR / "app-deployment.yaml").read_text(encoding="utf-8")
        config = (K8S_DIR / "app-configmap.yaml").read_text(encoding="utf-8")

        self.assertIn(f"ghcr.io/keregan/devops-notes-lab:{version}", deployment)
        self.assertIn(f'APP_VERSION: "{version}"', config)
        self.assertIn('REDIS_HOST: "redis"', config)

    def test_redis_is_persistent_pinned_and_internal(self):
        statefulset = (K8S_DIR / "redis-statefulset.yaml").read_text(
            encoding="utf-8"
        )
        service = (K8S_DIR / "redis-service.yaml").read_text(encoding="utf-8")
        network_policy = (K8S_DIR / "network-policy.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("kind: StatefulSet", statefulset)
        self.assertRegex(
            statefulset,
            r"image: redis:\d+\.\d+\.\d+-alpine@sha256:[a-f0-9]{64}",
        )
        self.assertIn("volumeClaimTemplates:", statefulset)
        self.assertIn("storage: 1Gi", statefulset)
        self.assertIn("clusterIP: None", service)
        self.assertIn("kind: NetworkPolicy", network_policy)
        self.assertIn("app.kubernetes.io/name: app", network_policy)
        self.assertIn("port: 6379", network_policy)

    def test_documentation_and_roadmap_cover_kubernetes(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        roadmap = (PROJECT_ROOT / "ROADMAP.md").read_text(encoding="utf-8")

        self.assertIn("kubectl apply -k k8s", readme)
        self.assertIn("port-forward service/app", readme)
        self.assertIn("- [x] 24. Подготовить Kubernetes-манифесты", roadmap)


if __name__ == "__main__":
    unittest.main()
