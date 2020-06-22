import io
from unittest import TestCase, mock

from bme280pi.sensor import Sensor


class FakeSMBus:
    def __init__(self, value):
        """
        This is a fake bus class (to replace SMBus).
        It records the value it is initialized with, and makes
        it accessible for checks. It also reports its chip ID and
        version as fake.
        """
        self.value = value

    @staticmethod
    def read_i2c_block_data(address, register, length, force=None):
        return "fake_chip_id", "fake_version"


class TestInitializeBus(TestCase):
    def test(self):
        # this test requires us to override the processor type and smbbus
        known_revisions = {'0002': 0,
                           '0003': 0,
                           '0004': 1,
                           '0005': 1,
                           '0006': 1,
                           '0007': 0,
                           '0008': 0,
                           '0009': 0,
                           '000d': 1,
                           '000e': 1,
                           '000f': 1,
                           '0010': 0,
                           '0011': 1,
                           '0012': 0,
                           'a01041': 1,
                           'a21041': 1,
                           '900092': 1,
                           '900093': 1,
                           'a02082': 1,
                           'a22082': 1,
                           '9000c1': 1,
                           'c03111': 1,
                           'abcdef': 1,
                           '0000': 1}

        for revision in known_revisions:
            m = mock.mock_open(read_data="\nRevision:" + revision + "\n")
            with mock.patch('builtins.open', m):
                with mock.patch('smbus.SMBus', FakeSMBus):
                    sensor = Sensor()
                    self.assertEqual(sensor.bus.value,
                                     known_revisions[revision])


class FakeDataBus:
    def __init__(self, starting_point=-1):
        """
        A further fake bus class (to replace SMBus).
        This version returns data that is a realistic representation
        of actual data
        """
        self.i_read = starting_point
        self.data = [['fake_chip_id', 'fake_version'],
                     [96, 110, 203, 104, 50, 0, 29, 145, 59, 215, 208, 11,
                      232, 38, 42, 255, 249, 255, 172, 38, 10, 216, 189, 16],
                     [75],
                     [129, 1, 0, 16, 44, 3, 30],
                     [76, 60, 128, 129, 49, 128, 94, 120]]

    def write_byte_data(self, address, register, value, force=None):
        pass

    def read_i2c_block_data(self, address, register, length, force=None):
        self.i_read += 1
        return self.data[self.i_read]


def initialize_fake_bus(*args, **kwargs):
    return FakeDataBus()


class TestSensor(TestCase):
    def test_get_data(self):
        Sensor._initialize_bus = initialize_fake_bus
        sensor = Sensor()
        self.assertEqual(sensor.chip_id, "fake_chip_id")
        self.assertEqual(sensor.chip_version, "fake_version")

        data = sensor.get_data()
        self.assertLess(abs(data['temperature'] - 24.65), 1e-4)
        self.assertLess(abs(data['pressure'] - 969.1056565652227), 1e-4)
        self.assertLess(abs(data['humidity'] - 41.07329061361983), 1e-4)

    def test_get_temperature(self):
        sensor = Sensor()
        temperature = sensor.get_temperature()
        self.assertLess(abs(temperature - 24.65), 1e-4)

    def test_get_pressure(self):
        sensor = Sensor()
        pressure = sensor.get_pressure()
        self.assertLess(abs(pressure - 969.1056565652227), 1e-4)

    def test_get_humidity(self):
        sensor = Sensor()
        humidity = sensor.get_humidity()
        self.assertLess(abs(humidity - 41.07329061361983), 1e-4)

        sensor = Sensor()
        humidity = sensor.get_humidity(relative=False)
        self.assertLess(abs(humidity - 0.009291279797753835), 1e-4)


class TestPrintSensor(TestCase):
    def test(self):
        Sensor._initialize_bus = initialize_fake_bus
        sensor = Sensor()
        self.assertEqual(sensor.chip_id, "fake_chip_id")
        self.assertEqual(sensor.chip_version, "fake_version")

        ref_message = "Temperature:  24.65 C\n" + \
                      "Humidity:     41.07 %\n" + \
                      "Pressure:     969.1 hPa\n"

        with mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            sensor.print_data()
            self.assertEqual(fake_out.getvalue(), ref_message)

    def test_print_with_absolute_humidity(self):
        sensor = Sensor()
        ref_message = "Temperature:  24.65 C\n" + \
                      "Humidity:     0.009291 kg / m^3\n" + \
                      "Pressure:     969.1 hPa\n"

        with mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            sensor.print_data(relative_humidity=False)
            self.assertEqual(fake_out.getvalue(), ref_message)
