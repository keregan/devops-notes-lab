import unittest

from gunicorn_config import load_settings


class GunicornConfigTestCase(unittest.TestCase):
    def test_default_settings(self):
        self.assertEqual(
            load_settings({}),
            {
                "workers": 2,
                "threads": 4,
                "timeout": 30,
                "graceful_timeout": 30,
            },
        )

    def test_environment_overrides(self):
        environment = {
            "GUNICORN_WORKERS": "3",
            "GUNICORN_THREADS": "8",
            "GUNICORN_TIMEOUT": "45",
            "GUNICORN_GRACEFUL_TIMEOUT": "20",
        }

        self.assertEqual(
            load_settings(environment),
            {
                "workers": 3,
                "threads": 8,
                "timeout": 45,
                "graceful_timeout": 20,
            },
        )

    def test_non_integer_value_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "GUNICORN_WORKERS must be an integer from 1 to 32",
        ):
            load_settings({"GUNICORN_WORKERS": "many"})

    def test_values_outside_safe_range_are_rejected(self):
        invalid_values = (
            ("GUNICORN_WORKERS", "0"),
            ("GUNICORN_WORKERS", "33"),
            ("GUNICORN_THREADS", "65"),
            ("GUNICORN_TIMEOUT", "301"),
            ("GUNICORN_GRACEFUL_TIMEOUT", "0"),
        )

        for variable, value in invalid_values:
            with (
                self.subTest(variable=variable, value=value),
                self.assertRaisesRegex(ValueError, variable),
            ):
                load_settings({variable: value})


if __name__ == "__main__":
    unittest.main()
