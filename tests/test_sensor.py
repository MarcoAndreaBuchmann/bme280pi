import builtins
import io
import warnings
from typing import Any
from unittest import TestCase, mock

from bme280pi.sensor import I2CException, Sensor


class FakeSMBus:
    def __init__(self, value: int) -> None:
        """
        This is a fake bus class (to replace SMBus).
        It records the value it is initialized with, and makes
        it accessible for checks. It also reports the chip ID of a BME280.
        """
        self.value = value

    @staticmethod
    def read_i2c_block_data(
        address: int, register: int, length: int, force: bool | None = None
    ) -> tuple[int, int]:
        return 0x60, 0


class TestInitializeBus(TestCase):
    def test(self) -> None:
        # this test requires us to override the processor type and smbbus
        # only the original Model B (revision 1) uses I2C bus 0
        known_revisions = {
            "0002": 0,
            "0003": 0,
            "0004": 1,
            "0005": 1,
            "0006": 1,
            "0007": 1,
            "0008": 1,
            "0009": 1,
            "000d": 1,
            "000e": 1,
            "000f": 1,
            "0010": 1,
            "0011": 1,
            "0012": 1,
            "a01041": 1,
            "a21041": 1,
            "900092": 1,
            "900093": 1,
            "a02082": 1,
            "a22082": 1,
            "9000c1": 1,
            "c03111": 1,
            "abcdef": 1,
            "0000": 1,
        }

        for revision in known_revisions:
            m = mock.mock_open(read_data="\nRevision:" + revision + "\n")
            with mock.patch("builtins.open", m):
                with mock.patch("smbus2.SMBus", FakeSMBus):
                    sensor = Sensor()
                    self.assertEqual(sensor.bus.value, known_revisions[revision])


class TestBusNumber(TestCase):
    def test_explicit_bus_number_skips_detection(self) -> None:
        with (
            mock.patch("smbus2.SMBus", FakeSMBus),
            mock.patch("bme280pi.sensor.detect_raspberry_pi_version") as detect,
        ):
            sensor = Sensor(bus_number=3)

        detect.assert_not_called()
        self.assertEqual(sensor.bus.value, 3)

    def test_explicit_bus_number_overrides_old_model_b(self) -> None:
        fake_open = mock.mock_open(read_data="Revision\t: 0002\n")
        with (
            mock.patch("smbus2.SMBus", FakeSMBus),
            mock.patch("builtins.open", fake_open),
        ):
            self.assertEqual(Sensor().bus.value, 0)
            self.assertEqual(Sensor(bus_number=1).bus.value, 1)


class FakeDataBus:
    def __init__(self, starting_point: int = -1) -> None:
        """
        A further fake bus class (to replace SMBus).
        This version returns data that is a realistic representation
        of actual data
        """
        self.i_read = starting_point
        self.data = [
            [0x60, 0],
            [
                96,
                110,
                203,
                104,
                50,
                0,
                29,
                145,
                59,
                215,
                208,
                11,
                232,
                38,
                42,
                255,
                249,
                255,
                172,
                38,
                10,
                216,
                189,
                16,
            ],
            [75],
            [129, 1, 0, 16, 44, 3, 30],
            [76, 60, 128, 129, 49, 128, 94, 120],
        ]

    def write_byte_data(
        self, address: int, register: int, value: int, force: bool | None = None
    ) -> None:
        pass

    def read_i2c_block_data(
        self, address: int, register: int, length: int, force: bool | None = None
    ) -> list[int]:
        self.i_read += 1
        return self.data[self.i_read]


class FakeRegisterBus:
    """
    A fake bus that returns realistic data depending on the register that is
    read, and records every register that is read or written.
    """

    def __init__(self, chip_id: int = 0x60) -> None:
        reference = FakeDataBus().data
        self.registers: dict[int, list[int]] = {
            0xD0: [chip_id, 0],
            0x88: reference[1],
            0xA1: reference[2],
            0xE1: reference[3],
            0xF7: reference[4],
        }
        self.reads: list[int] = []
        self.writes: list[tuple[int, int]] = []
        self.closed = False

    def write_byte_data(
        self, address: int, register: int, value: int, force: bool | None = None
    ) -> None:
        self.writes.append((register, value))

    def read_i2c_block_data(
        self, address: int, register: int, length: int, force: bool | None = None
    ) -> list[int]:
        self.reads.append(register)
        return self.registers[register]

    def close(self) -> None:
        self.closed = True


def use_bus(bus: Any) -> Any:
    """Patch Sensor._initialize_bus so that the sensor uses the given bus."""

    def initialize_bus(*args: Any, **kwargs: Any) -> Any:
        return bus

    return mock.patch("bme280pi.Sensor._initialize_bus", initialize_bus)


class FileNotFoundSMBus:
    def __init__(self, bus_address: int) -> None:
        """
        This fake bus class raises a FileNotFoundError, because that's what
        SMBus can do in case I2C is not configured.
        """
        raise FileNotFoundError("No such file or directory")


def initialize_fake_bus(*args: Any, **kwargs: Any) -> Any:
    return FakeDataBus()


class TestSensor(TestCase):
    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_data(self) -> None:
        sensor = Sensor()
        self.assertEqual(sensor.chip_id, 0x60)
        self.assertEqual(sensor.chip_version, 0)

        data = sensor.get_data()
        self.assertLess(abs(data["temperature"] - 24.65), 1e-4)
        self.assertLess(abs(data["pressure"] - 969.1056565652227), 1e-4)
        self.assertLess(abs(data["humidity"] - 41.07329061361983), 1e-4)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_temperature(self) -> None:
        sensor = Sensor()
        temperature = sensor.get_temperature()
        self.assertLess(abs(temperature - 24.65), 1e-4)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_pressure(self) -> None:
        sensor = Sensor()
        pressure = sensor.get_pressure()
        self.assertLess(abs(pressure - 969.1056565652227), 1e-4)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_pressure_above_sea_level(self) -> None:
        sensor = Sensor()
        pressure = sensor.get_pressure(
            height_above_sea_level=440,
            as_pressure_at_sea_level=True,
        )
        self.assertLess(abs(pressure - 1019.0420210), 1e-4)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_pressure_without_height_above_sea_level(self) -> None:
        sensor = Sensor()
        with self.assertRaises(ValueError):
            sensor.get_pressure(
                height_above_sea_level=None, as_pressure_at_sea_level=True
            )

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_get_humidity(self) -> None:
        sensor = Sensor()
        humidity = sensor.get_humidity()
        self.assertLess(abs(humidity - 41.07329061361983), 1e-4)

        sensor = Sensor()
        humidity = sensor.get_humidity(relative=False)
        self.assertLess(abs(humidity - 0.009291279797753835), 1e-4)

    def test_unconfigured_i2c(self) -> None:
        fake_open = mock.mock_open(read_data="Revision\t: 0000\n")
        with (
            mock.patch("smbus2.SMBus", FileNotFoundSMBus),
            mock.patch(f"{builtins.__name__}.open", fake_open),
        ):
            with self.assertRaises(I2CException):
                Sensor()


class TestCalibrationIsReadOnce(TestCase):
    def test(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            sensor = Sensor()
            first = sensor.get_data()
            second = sensor.get_data()

        self.assertEqual(first, second)
        self.assertLess(abs(first["temperature"] - 24.65), 1e-4)
        self.assertEqual(bus.reads.count(0x88), 1)
        self.assertEqual(bus.reads.count(0xA1), 1)
        self.assertEqual(bus.reads.count(0xE1), 1)
        self.assertEqual(bus.reads.count(0xF7), 2)

    def test_every_getter_makes_a_measurement(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            sensor = Sensor()
            sensor.get_temperature()
            sensor.get_pressure()
            sensor.get_humidity()

        self.assertEqual(bus.reads.count(0xF7), 3)
        self.assertEqual(bus.reads.count(0x88), 1)


class TestOversampling(TestCase):
    def test_default(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            sensor = Sensor()
            sensor.get_data()

        self.assertEqual(
            sensor.oversampling, {"temperature": 2, "pressure": 2, "humidity": 2}
        )
        # ctrl_hum (0xF2) and ctrl_meas (0xF4): osrs_t = 2, osrs_p = 2, forced mode
        self.assertEqual(bus.writes, [(0xF2, 2), (0xF4, (2 << 5) | (2 << 2) | 1)])

    def test_custom(self) -> None:
        bus = FakeRegisterBus()
        settings = {"temperature": 1, "pressure": 3, "humidity": 5}
        with use_bus(bus):
            sensor = Sensor(oversampling=settings)
            sensor.get_data()

        self.assertEqual(bus.writes, [(0xF2, 5), (0xF4, (1 << 5) | (3 << 2) | 1)])

        # later changes to the dictionary do not affect the sensor
        settings["pressure"] = 0
        self.assertEqual(sensor.oversampling["pressure"], 3)

    def test_invalid_settings_are_rejected_before_using_the_bus(self) -> None:
        with mock.patch("bme280pi.Sensor._initialize_bus") as initialize_bus:
            with self.assertRaises(ValueError):
                Sensor(oversampling={"temperature": 9, "pressure": 2, "humidity": 2})
            with self.assertRaises(KeyError):
                Sensor(oversampling={"temperature": 2})
        initialize_bus.assert_not_called()


class TestChipId(TestCase):
    def test_bme280_does_not_warn(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with use_bus(FakeRegisterBus(chip_id=0x60)):
                Sensor()

    def test_bmp280_warns_about_missing_humidity_sensor(self) -> None:
        for chip_id in (0x56, 0x57, 0x58):
            with use_bus(FakeRegisterBus(chip_id=chip_id)):
                with self.assertWarnsRegex(UserWarning, "BMP280.*no humidity sensor"):
                    Sensor()

    def test_unknown_chip_warns(self) -> None:
        with use_bus(FakeRegisterBus(chip_id=0x61)):
            with self.assertWarns(UserWarning) as context:
                Sensor(address=0x77)

        message = str(context.warning)
        self.assertIn("0x61", message)
        self.assertIn("0x77", message)
        self.assertNotIn("BMP280", message)

    def test_warning_points_at_the_caller(self) -> None:
        with use_bus(FakeRegisterBus(chip_id=0x58)):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                Sensor()

        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0].filename, __file__)


class TestClose(TestCase):
    def test_close(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            sensor = Sensor()

        self.assertFalse(bus.closed)
        sensor.close()
        self.assertTrue(bus.closed)

    def test_context_manager(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            with Sensor() as sensor:
                data = sensor.get_data()
                self.assertFalse(bus.closed)

        self.assertLess(abs(data["temperature"] - 24.65), 1e-4)
        self.assertTrue(bus.closed)

    def test_context_manager_closes_on_error(self) -> None:
        bus = FakeRegisterBus()
        with use_bus(bus):
            with self.assertRaises(RuntimeError):
                with Sensor():
                    raise RuntimeError("something went wrong")

        self.assertTrue(bus.closed)


class TestPrintSensor(TestCase):
    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test(self) -> None:
        sensor = Sensor()
        self.assertEqual(sensor.chip_id, 0x60)
        self.assertEqual(sensor.chip_version, 0)

        ref_message = (
            "Temperature:  24.65 C\n"
            + "Humidity:     41.07 %\n"
            + "Pressure:     969.1 hPa\n"
        )

        with mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            sensor.print_data()
            self.assertEqual(fake_out.getvalue(), ref_message)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_print_with_absolute_humidity(self) -> None:
        sensor = Sensor()
        ref_message = (
            "Temperature:  24.65 C\n"
            + "Humidity:     0.009291 kg / m^3\n"
            + "Pressure:     969.1 hPa\n"
        )

        with mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            sensor.print_data(relative_humidity=False)
            self.assertEqual(fake_out.getvalue(), ref_message)

    @mock.patch("bme280pi.Sensor._initialize_bus", initialize_fake_bus)
    def test_print_with_zero_values(self) -> None:
        sensor = Sensor()
        zero_reading = {"temperature": 0.0, "pressure": 1000.0, "humidity": 0.0}

        with (
            mock.patch.object(sensor, "get_data", return_value=zero_reading),
            mock.patch("sys.stdout", new_callable=io.StringIO) as fake_out,
        ):
            sensor.print_data()
            sensor.print_data(relative_humidity=False)

        self.assertIn("Temperature:  0.0 C", fake_out.getvalue())
        self.assertIn("Humidity:     0.0 %", fake_out.getvalue())
