from unittest import TestCase, mock

from bme280pi.raspberry_pi_version import (detect_raspberry_pi_version,
                                           get_list_of_revisions)


def raise_exception(*args, **kwargs):
    raise FileNotFoundError


class test_detect_raspberry_pi_version(TestCase):
    def test(self):
        known_revisions = get_list_of_revisions()

        known_revisions['bad_id'] = "Unknown"

        for revision in known_revisions:
            m = mock.mock_open(read_data="\nRevision:" + revision + "\n")
            with mock.patch('builtins.open', m):
                self.assertEqual(detect_raspberry_pi_version(),
                                 known_revisions[revision])

    def test_exception(self):
        m = raise_exception
        with mock.patch('builtins.open', m):
            with self.assertWarns(Warning):
                self.assertEqual(detect_raspberry_pi_version(), "Unknown")
