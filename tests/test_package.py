from unittest import TestCase

import bme280pi
from bme280pi import I2CException, Sensor


class TestPackage(TestCase):
    def test_version(self) -> None:
        self.assertIsInstance(bme280pi.__version__, str)
        self.assertTrue(bme280pi.__version__)

    def test_all_names_are_exported(self) -> None:
        for name in bme280pi.__all__:
            self.assertTrue(hasattr(bme280pi, name), name)

    def test_public_classes(self) -> None:
        self.assertIs(Sensor, bme280pi.sensor.Sensor)
        self.assertIs(I2CException, bme280pi.sensor.I2CException)
        self.assertTrue(issubclass(I2CException, Exception))
