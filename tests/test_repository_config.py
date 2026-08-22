import json
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPENDABOT_CONFIG = PROJECT_ROOT / ".github" / "dependabot.yml"
GITHUB_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
GITLAB_WORKFLOW = PROJECT_ROOT / ".gitlab-ci.yml"
DEV_REQUIREMENTS = PROJECT_ROOT / "requirements-dev.txt"
VERSION_FILE = PROJECT_ROOT / "VERSION"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
BASE_COMPOSE = PROJECT_ROOT / "docker-compose.yml"
MONITORING_COMPOSE = PROJECT_ROOT / "docker-compose.monitoring.yml"
PROMETHEUS_CONFIG = PROJECT_ROOT / "monitoring" / "prometheus" / "prometheus.yml"
GRAFANA_DATASOURCE = (
    PROJECT_ROOT
    / "monitoring"
    / "grafana"
    / "provisioning"
    / "datasources"
    / "prometheus.yml"
)
GRAFANA_DASHBOARD = (
    PROJECT_ROOT / "monitoring" / "grafana" / "dashboards" / "devops-notes-lab.json"
)


class DependabotConfigTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = DEPENDABOT_CONFIG.read_text(encoding="utf-8")

    def test_uses_current_configuration_schema(self):
        self.assertRegex(self.config, r"(?m)^version: 2$")

    def test_monitors_python_and_github_actions(self):
        ecosystems = re.findall(
            r'package-ecosystem: "([^"]+)"',
            self.config,
        )

        self.assertCountEqual(ecosystems, ["pip", "github-actions"])

    def test_every_ecosystem_has_weekly_root_schedule(self):
        entries = self.config.split("  - package-ecosystem:")[1:]

        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertIn('directory: "/"', entry)
            self.assertIn('interval: "weekly"', entry)
            self.assertIn('timezone: "Europe/Moscow"', entry)
            self.assertIn("open-pull-requests-limit: 5", entry)


class DependencyAuditConfigTestCase(unittest.TestCase):
    audit_command = (
        "python -m pip_audit --strict --progress-spinner off -r requirements.txt"
    )

    def test_pip_audit_version_is_pinned(self):
        requirements = DEV_REQUIREMENTS.read_text(encoding="utf-8")

        self.assertRegex(requirements, r"(?m)^pip-audit==\d+\.\d+\.\d+$")

    def test_both_ci_pipelines_run_dependency_audit(self):
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(self.audit_command, github_workflow)
        self.assertIn(self.audit_command, gitlab_workflow)


class MonitoringConfigTestCase(unittest.TestCase):
    def test_prometheus_lifecycle_api_is_disabled(self):
        compose = MONITORING_COMPOSE.read_text(encoding="utf-8")

        self.assertNotIn("--web.enable-lifecycle", compose)

    def test_grafana_admin_password_is_required(self):
        compose = MONITORING_COMPOSE.read_text(encoding="utf-8")
        env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("${GRAFANA_ADMIN_PASSWORD:?", compose)
        self.assertNotIn("change-me", compose)
        self.assertRegex(env_example, r"(?m)^GRAFANA_ADMIN_PASSWORD=$")
        self.assertIn("GRAFANA_ADMIN_PASSWORD: ci-only-password", github_workflow)
        self.assertIn("GRAFANA_ADMIN_PASSWORD: ci-only-password", gitlab_workflow)

    def test_published_ports_are_bound_to_loopback(self):
        base_compose = BASE_COMPOSE.read_text(encoding="utf-8")
        monitoring_compose = MONITORING_COMPOSE.read_text(encoding="utf-8")

        self.assertIn(
            '"127.0.0.1:${APP_PORT:-8084}:8000"',
            base_compose,
        )
        self.assertIn(
            '"127.0.0.1:${PROMETHEUS_PORT:-9090}:9090"',
            monitoring_compose,
        )
        self.assertIn(
            '"127.0.0.1:${GRAFANA_PORT:-3000}:3000"',
            monitoring_compose,
        )

    def test_monitoring_images_are_pinned_by_version_and_digest(self):
        compose = MONITORING_COMPOSE.read_text(encoding="utf-8")

        self.assertRegex(
            compose,
            r"image: prom/prometheus:v\d+\.\d+\.\d+@sha256:[a-f0-9]{64}",
        )
        self.assertRegex(
            compose,
            r"image: grafana/grafana:\d+\.\d+\.\d+@sha256:[a-f0-9]{64}",
        )

    def test_prometheus_scrapes_application_metrics(self):
        prometheus = PROMETHEUS_CONFIG.read_text(encoding="utf-8")

        self.assertIn('job_name: "devops-notes-lab"', prometheus)
        self.assertIn('metrics_path: "/metrics"', prometheus)
        self.assertIn('"app:8000"', prometheus)

    def test_grafana_uses_provisioned_prometheus_datasource(self):
        datasource = GRAFANA_DATASOURCE.read_text(encoding="utf-8")

        self.assertIn("type: prometheus", datasource)
        self.assertIn("uid: prometheus", datasource)
        self.assertIn("url: http://prometheus:9090", datasource)
        self.assertIn("isDefault: true", datasource)

    def test_dashboard_contains_application_metrics(self):
        dashboard = json.loads(GRAFANA_DASHBOARD.read_text(encoding="utf-8"))
        expressions = {
            target["expr"]
            for panel in dashboard["panels"]
            for target in panel.get("targets", [])
        }

        self.assertEqual(dashboard["uid"], "devops-notes-lab")
        self.assertIn("devops_notes_lab_up", expressions)
        self.assertIn("devops_notes_lab_redis_up", expressions)
        self.assertIn("devops_notes_lab_visits_total", expressions)

    def test_both_ci_pipelines_validate_monitoring_compose(self):
        command = (
            "docker compose -f docker-compose.yml "
            "-f docker-compose.monitoring.yml config --quiet"
        )
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(command, github_workflow)
        self.assertIn(command, gitlab_workflow)


class ReleaseConfigTestCase(unittest.TestCase):
    def test_project_version_is_synchronized(self):
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
        files_with_version = (
            PROJECT_ROOT / ".env.example",
            PROJECT_ROOT / "docker-compose.yml",
            GITHUB_WORKFLOW,
            GITLAB_WORKFLOW,
        )

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        for path in files_with_version:
            self.assertIn(version, path.read_text(encoding="utf-8"))

    def test_changelog_contains_current_version(self):
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
        changelog = CHANGELOG.read_text(encoding="utf-8")

        self.assertIn("## [Unreleased]", changelog)
        self.assertIn(f"## [{version}]", changelog)

    def test_release_workflow_validates_tag_and_creates_release(self):
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('      - "v*.*.*"', workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("project_version=", workflow)
        self.assertIn("gh release create", workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertIn("--generate-notes", workflow)


if __name__ == "__main__":
    unittest.main()
