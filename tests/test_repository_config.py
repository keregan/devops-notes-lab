import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPENDABOT_CONFIG = PROJECT_ROOT / ".github" / "dependabot.yml"


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


if __name__ == "__main__":
    unittest.main()
