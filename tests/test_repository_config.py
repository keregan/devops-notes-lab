import json
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ENTRYPOINT = PROJECT_ROOT / "app.py"
APPLICATION_PACKAGE = PROJECT_ROOT / "devops_notes_lab"
DEPENDABOT_CONFIG = PROJECT_ROOT / ".github" / "dependabot.yml"
GITHUB_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "release.yml"
GITLAB_WORKFLOW = PROJECT_ROOT / ".gitlab-ci.yml"
DEV_REQUIREMENTS = PROJECT_ROOT / "requirements-dev.txt"
PYPROJECT_CONFIG = PROJECT_ROOT / "pyproject.toml"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"
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


class GithubActionsSecurityTestCase(unittest.TestCase):
    def test_external_actions_are_pinned_to_full_commit_sha(self):
        workflows = (GITHUB_WORKFLOW, RELEASE_WORKFLOW)

        for path in workflows:
            workflow = path.read_text(encoding="utf-8")
            action_references = re.findall(
                r"(?m)^\s+uses:\s+(\S+)",
                workflow,
            )

            for reference in action_references:
                if reference.startswith("./"):
                    continue
                with self.subTest(workflow=path.name, reference=reference):
                    commit_sha = reference.rsplit("@", maxsplit=1)[-1]
                    self.assertRegex(commit_sha, r"^[a-f0-9]{40}$")


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


class RuffConfigTestCase(unittest.TestCase):
    def test_extended_rule_sets_are_enabled(self):
        config = PYPROJECT_CONFIG.read_text(encoding="utf-8")

        self.assertIn(
            'select = ["E4", "E7", "E9", "F", "I", "B", "UP", "SIM", "RUF"]',
            config,
        )

    def test_coverage_includes_runtime_modules(self):
        config = PYPROJECT_CONFIG.read_text(encoding="utf-8")

        self.assertIn(
            'source = ["app", "devops_notes_lab", "gunicorn_config"]',
            config,
        )


class ApplicationStructureTestCase(unittest.TestCase):
    def test_entrypoint_remains_small_and_backwards_compatible(self):
        entrypoint = APP_ENTRYPOINT.read_text(encoding="utf-8")

        self.assertLessEqual(len(entrypoint.splitlines()), 20)
        self.assertIn("from devops_notes_lab import create_app", entrypoint)
        self.assertIn("app = create_app()", entrypoint)
        self.assertNotIn("@application", entrypoint)

    def test_application_responsibilities_are_split_into_modules(self):
        expected_modules = {
            "__init__.py",
            "http.py",
            "logging_config.py",
            "observability.py",
            "redis_client.py",
            "routes.py",
        }

        self.assertSetEqual(
            {path.name for path in APPLICATION_PACKAGE.glob("*.py")},
            expected_modules,
        )


class MonitoringConfigTestCase(unittest.TestCase):
    def test_docker_build_context_uses_runtime_allowlist(self):
        patterns = [
            line
            for raw_line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
            if (line := raw_line.strip()) and not line.startswith("#")
        ]
        included_paths = {pattern for pattern in patterns if pattern.startswith("!")}

        self.assertEqual(patterns[0], "*")
        self.assertSetEqual(
            included_paths,
            {
                "!Dockerfile",
                "!requirements.txt",
                "!app.py",
                "!gunicorn_config.py",
                "!VERSION",
                "!devops_notes_lab",
                "!devops_notes_lab/**",
                "!static",
                "!static/**",
                "!templates",
                "!templates/**",
            },
        )

    def test_container_includes_runtime_modules(self):
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")

        self.assertIn(
            "COPY app.py gunicorn_config.py ./",
            dockerfile,
        )
        self.assertIn("COPY devops_notes_lab ./devops_notes_lab", dockerfile)
        self.assertIn(
            'CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]',
            dockerfile,
        )

    def test_gunicorn_defaults_are_exposed_through_compose(self):
        compose = BASE_COMPOSE.read_text(encoding="utf-8")
        env_example = ENV_EXAMPLE.read_text(encoding="utf-8")
        defaults = {
            "GUNICORN_WORKERS": "2",
            "GUNICORN_THREADS": "4",
            "GUNICORN_TIMEOUT": "30",
            "GUNICORN_GRACEFUL_TIMEOUT": "30",
        }

        for variable, default in defaults.items():
            with self.subTest(variable=variable):
                self.assertIn(f"${{{variable}:-{default}}}", compose)
                self.assertRegex(
                    env_example,
                    rf"(?m)^{variable}={default}$",
                )

    def test_prometheus_lifecycle_api_is_disabled(self):
        compose = MONITORING_COMPOSE.read_text(encoding="utf-8")

        self.assertNotIn("--web.enable-lifecycle", compose)

    def test_prometheus_storage_retention_is_limited(self):
        compose = MONITORING_COMPOSE.read_text(encoding="utf-8")
        env_example = ENV_EXAMPLE.read_text(encoding="utf-8")

        self.assertIn(
            "--storage.tsdb.retention.time=${PROMETHEUS_RETENTION_TIME:-7d}",
            compose,
        )
        self.assertIn(
            "--storage.tsdb.retention.size=${PROMETHEUS_RETENTION_SIZE:-1GB}",
            compose,
        )
        self.assertRegex(env_example, r"(?m)^PROMETHEUS_RETENTION_TIME=7d$")
        self.assertRegex(env_example, r"(?m)^PROMETHEUS_RETENTION_SIZE=1GB$")

    def test_application_container_is_hardened(self):
        compose = BASE_COMPOSE.read_text(encoding="utf-8")

        self.assertRegex(compose, r"(?m)^    read_only: true$")
        self.assertRegex(compose, r"(?m)^    cap_drop:\n      - ALL$")
        self.assertRegex(
            compose,
            r"(?m)^    security_opt:\n      - no-new-privileges:true$",
        )
        self.assertIn("/tmp:rw,noexec,nosuid,size=16m,mode=1777", compose)

    def test_both_ci_pipelines_verify_container_hardening(self):
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        for workflow in (github_workflow, gitlab_workflow):
            self.assertIn("HostConfig.ReadonlyRootfs", workflow)
            self.assertIn("HostConfig.CapDrop", workflow)
            self.assertIn("HostConfig.SecurityOpt", workflow)
            self.assertIn("test ! -w /app && test -w /tmp", workflow)

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
        self.assertIn(
            "sum(rate(devops_notes_lab_http_requests_total[5m]))",
            expressions,
        )
        self.assertIn(
            "sum(rate(devops_notes_lab_http_errors_total[5m]))",
            expressions,
        )
        self.assertTrue(
            any(
                "devops_notes_lab_http_request_duration_seconds_sum" in expression
                for expression in expressions
            )
        )

    def test_both_ci_pipelines_validate_monitoring_compose(self):
        compose = (
            "docker compose -f docker-compose.yml -f docker-compose.monitoring.yml"
        )
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(f"{compose} config --quiet", github_workflow)
        self.assertIn(f"{compose} config --quiet", gitlab_workflow)

    def test_both_ci_pipelines_run_and_check_monitoring_stack(self):
        compose = (
            "docker compose -f docker-compose.yml -f docker-compose.monitoring.yml"
        )
        github_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        gitlab_workflow = GITLAB_WORKFLOW.read_text(encoding="utf-8")

        for workflow in (github_workflow, gitlab_workflow):
            self.assertIn(f"{compose} up -d --wait --wait-timeout 120", workflow)
            self.assertIn("http://localhost:3000/api/health", workflow)
            self.assertIn("/api/v1/targets", workflow)
            self.assertIn('"job":"devops-notes-lab"', workflow)
            self.assertIn('"health":"up"', workflow)

        self.assertIn("http://localhost:9090/-/ready", github_workflow)
        self.assertIn("http://localhost:9090/api/v1/targets", github_workflow)
        self.assertIn('"http://localhost:9090$1"', gitlab_workflow)
        self.assertIn("prometheus_get /-/ready", gitlab_workflow)
        self.assertIn("prometheus_get /api/v1/targets", gitlab_workflow)


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

    def test_release_publishes_versioned_image_to_ghcr(self):
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")

        self.assertIn("REGISTRY: ghcr.io", workflow)
        self.assertIn("IMAGE_NAME: ${{ github.repository }}", workflow)
        self.assertIn("packages: write", workflow)
        self.assertIn('docker login "$REGISTRY"', workflow)
        self.assertIn("--password-stdin", workflow)
        self.assertIn('--tag "${image}:${PROJECT_VERSION}"', workflow)
        self.assertIn('--tag "${image}:latest"', workflow)
        self.assertIn("docker manifest inspect", workflow)
        self.assertIn("org.opencontainers.image.source", dockerfile)
        self.assertIn("org.opencontainers.image.revision", workflow)
        self.assertIn("org.opencontainers.image.version", workflow)
        self.assertLess(
            workflow.index("docker manifest inspect"),
            workflow.index("gh release create"),
        )

    def test_release_requires_successful_reusable_ci(self):
        ci_workflow = GITHUB_WORKFLOW.read_text(encoding="utf-8")
        release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

        self.assertRegex(ci_workflow, r"(?m)^  workflow_call:$")
        self.assertIn("quality-gate:", release_workflow)
        self.assertIn("uses: ./.github/workflows/ci.yml", release_workflow)
        self.assertIn("needs: quality-gate", release_workflow)
        self.assertIn("needs: publish-image", release_workflow)
        self.assertRegex(
            release_workflow,
            r"(?m)^permissions:\n  contents: read$",
        )
        self.assertRegex(
            release_workflow,
            r"(?m)^    permissions:\n      contents: write$",
        )


if __name__ == "__main__":
    unittest.main()
