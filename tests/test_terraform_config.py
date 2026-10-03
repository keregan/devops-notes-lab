import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_DIR = PROJECT_ROOT / "terraform" / "test"


class TerraformConfigTestCase(unittest.TestCase):
    def test_versions_are_constrained_and_provider_is_pinned(self):
        versions = (TERRAFORM_DIR / "versions.tf").read_text(encoding="utf-8")

        self.assertIn('required_version = ">= 1.16.0, < 2.0.0"', versions)
        self.assertIn('source  = "hashicorp/kubernetes"', versions)
        self.assertRegex(versions, r'version = "\d+\.\d+\.\d+"')

    def test_test_namespace_has_quota_and_default_limits(self):
        config = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")

        self.assertIn('resource "kubernetes_namespace_v1" "test"', config)
        self.assertIn('resource "kubernetes_resource_quota_v1" "test"', config)
        self.assertIn('resource "kubernetes_limit_range_v1" "test"', config)
        self.assertIn('environment                    = "test"', config)
        self.assertIn('"requests.storage"     = "2Gi"', config)

    def test_existing_kubernetes_manifests_are_reused(self):
        config = (TERRAFORM_DIR / "main.tf").read_text(encoding="utf-8")
        expected = {
            "app-configmap.yaml",
            "app-deployment.yaml",
            "app-service.yaml",
            "network-policy.yaml",
            "redis-service.yaml",
            "redis-statefulset.yaml",
        }

        for manifest in expected:
            with self.subTest(manifest=manifest):
                self.assertIn(f'"{manifest}"', config)

        self.assertIn('resource "kubernetes_manifest" "workloads"', config)
        self.assertIn('file("${path.module}/../../k8s/${filename}")', config)
        self.assertIn("namespace = var.namespace", config)

    def test_state_and_local_variables_are_ignored(self):
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertRegex(gitignore, r"(?m)^\.terraform/$")
        self.assertRegex(gitignore, r"(?m)^\*\.tfstate$")
        self.assertRegex(gitignore, r"(?m)^\*\.tfvars$")
        self.assertIn("!*.tfvars.example", gitignore)

    def test_both_ci_systems_validate_terraform(self):
        github = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        gitlab = (PROJECT_ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")

        self.assertRegex(
            github,
            r"hashicorp/setup-terraform@[a-f0-9]{40}",
        )
        self.assertIn('terraform_version: "1.16.5"', github)
        self.assertIn("working-directory: terraform/test", github)
        self.assertIn("terraform_validate:", gitlab)
        self.assertRegex(
            gitlab,
            r"hashicorp/terraform:\d+\.\d+\.\d+@sha256:[a-f0-9]{64}",
        )

        for pipeline in (github, gitlab):
            self.assertIn("terraform fmt -check -recursive", pipeline)
            self.assertIn("terraform init -backend=false", pipeline)
            self.assertIn("terraform validate", pipeline)

    def test_documentation_and_roadmap_cover_terraform(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        roadmap = (PROJECT_ROOT / "ROADMAP.md").read_text(encoding="utf-8")

        self.assertIn("terraform -chdir=terraform/test plan", readme)
        self.assertIn("terraform -chdir=terraform/test destroy", readme)
        self.assertIn("- [x] 25. Описать тестовую инфраструктуру", roadmap)


if __name__ == "__main__":
    unittest.main()
