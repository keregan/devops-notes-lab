import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPENDABOT_CONFIG = PROJECT_ROOT / ".github" / "dependabot.yml"
GITHUB_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
GITLAB_WORKFLOW = PROJECT_ROOT / ".gitlab-ci.yml"
DEV_REQUIREMENTS = PROJECT_ROOT / "requirements-dev.txt"


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


if __name__ == "__main__":
    unittest.main()
