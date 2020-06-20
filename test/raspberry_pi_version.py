import mock
import unittest

from bme280pi.raspberry_pi_version import detect_raspberry_pi_version


def raise_exception(*args, **kwargs):
    raise FileNotFoundError


class test_detect_raspberry_pi_version(unittest.TestCase):
    def test(self):
        known_revisions = {'0002': 'Model B R1',
                           '0003': 'Model B R1',
                           '0004': 'Model B R2',
                           '0005': 'Model B R2',
                           '0006': 'Model B R2',
                           '0007': 'Model A',
                           '0008': 'Model A',
                           '0009': 'Model A',
                           '000d': 'Model B R2',
                           '000e': 'Model B R2',
                           '000f': 'Model B R2',
                           '0010': 'Model B+',
                           '0011': 'Compute Module',
                           '0012': 'Model A+',
                           'a01041': 'Pi 2 Model B',
                           'a21041': 'Pi 2 Model B',
                           '900092': 'Pi Zero',
                           '900093': 'Pi Zero',
                           'a02082': 'Pi 3 Model B',
                           'a22082': 'Pi 3 Model B',
                           '9000c1': 'Pi Zero W',
                           'c03111': 'Pi 4 Model B',
                           'abcdef': 'TestModel',
                           '0000': 'Unknown',
                           'DeliberateError': "Unknown"}

        for revision in known_revisions:
            m = mock.mock_open(read_data="\nRevision:" + revision + "\n")
            with mock.patch('builtins.open', m):
                self.assertEqual(detect_raspberry_pi_version(),
                                 known_revisions[revision])

        m = raise_exception
        with mock.patch('builtins.open', m):
            with self.assertWarns(Warning):
                self.assertEqual(detect_raspberry_pi_version(), "Unknown")
