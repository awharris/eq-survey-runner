import unittest

from app import settings


class TestSettings(unittest.TestCase):

    def test_ensure_min_returns_min(self):
        minimum = 1000
        value = 1
        self.assertEqual(minimum, settings.ensure_min(value, minimum))

    def test_ensure_min_returns_value(self):
        minimum = 1000
        value = 10000
        self.assertEqual(value, settings.ensure_min(value, minimum))

    def test_get_application_version_from_file(self):
        settings.EQ_APPLICATION_VERSION_PATH = '.application-version'
        self.assertIsNotNone(settings.get_application_version_from_file())

    def test_missing_get_application_version_from_file(self):
        settings.EQ_APPLICATION_VERSION_PATH = '.missing-application-version'
        self.assertEqual(None, settings.get_application_version_from_file())

if __name__ == '__main__':
    unittest.main()
