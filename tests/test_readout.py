from typing import Any
from unittest import TestCase, mock

from bme280pi.readout import (
    extract_raw_values,
    extract_values,
    get_character,
    get_modified,
    get_short,
    get_unsigned_character,
    get_unsigned_short,
    improve_humidity_measurement,
    improve_pressure_measurement,
    improve_temperature_measurement,
    measurement_time_ms,
    process_calibration_data,
    read_calibration_data,
    read_raw_sensor,
    read_sensor,
    validate_oversampling,
)
from tests.test_sensor import FakeDataBus


class FakeRecordingBus:
    """
    This is a fake bus class (to simulate SMBus for tests)
    This "bus" class records all commands, which allows tests
    to check that the right sequence is called.
    """

    def __init__(self) -> None:
        """
        Initialize a fake bus class
        """
        self.commands: list[list[Any]] = []

    def write_byte_data(
        self, address: int, register: int, value: int, force: bool | None = None
    ) -> None:
        self.commands.append(["write_byte_data", address, register, value, force])

    def read_i2c_block_data(
        self, address: int, register: int, length: int, force: bool | None = None
    ) -> int:
        self.commands.append(["read_i2c_block_data", address, register, length, force])
        return len(self.commands)


class TestGetShort(TestCase):
    def test(self) -> None:
        test_result = get_short(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result - 385), 1e-6)


class TestGetUnsignedshort(TestCase):
    def test(self) -> None:
        test_result = get_unsigned_short(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result - 385), 1e-6)


class TestGetCharacter(TestCase):
    def test(self) -> None:
        test_result = get_character(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result + 127), 1e-6)


class TestGetUnsignedCharacter(TestCase):
    def test(self) -> None:
        test_result = get_unsigned_character(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result - 129), 1e-6)


class TestReadRawSensor(TestCase):
    def test(self) -> None:
        bus = FakeRecordingBus()
        cals, data = read_raw_sensor(
            bus=bus,
            address=0xFFFFF,
            oversampling={"temperature": 2, "pressure": 2, "humidity": 2},
            reg_data=0xEEEEE,
        )
        self.assertEqual(cals[0], 3)
        self.assertEqual(cals[1], 4)
        self.assertEqual(cals[2], 5)
        self.assertEqual(data, 6)

        correct_commands = [
            ["write_byte_data", 0xFFFFF, 242, 2, None],
            ["write_byte_data", 0xFFFFF, 244, 73, None],
            ["read_i2c_block_data", 0xFFFFF, 136, 24, None],
            ["read_i2c_block_data", 0xFFFFF, 161, 1, None],
            ["read_i2c_block_data", 0xFFFFF, 225, 7, None],
            ["read_i2c_block_data", 0xFFFFF, 0xEEEEE, 8, None],
        ]

        for i, correct_value in enumerate(correct_commands):
            # check type of command
            self.assertEqual(bus.commands[i][0], correct_value[0])
            # check address
            self.assertEqual(bus.commands[i][1], correct_value[1])
            # check register
            self.assertEqual(bus.commands[i][2], correct_value[2])
            # check length or value
            self.assertEqual(bus.commands[i][3], correct_value[3])
            # check whether force was set
            self.assertEqual(bus.commands[i][4], correct_value[4])


class TestReadCalibrationData(TestCase):
    def test(self) -> None:
        bus = FakeRecordingBus()
        cals = read_calibration_data(bus=bus, address=0xFFFFF)
        self.assertEqual(cals, [1, 2, 3])
        self.assertEqual(
            [command[:4] for command in bus.commands],
            [
                ["read_i2c_block_data", 0xFFFFF, 0x88, 24],
                ["read_i2c_block_data", 0xFFFFF, 0xA1, 1],
                ["read_i2c_block_data", 0xFFFFF, 0xE1, 7],
            ],
        )


class TestMeasurementTime(TestCase):
    @staticmethod
    def settings(temperature: int, pressure: int, humidity: int) -> dict[str, int]:
        return {"temperature": temperature, "pressure": pressure, "humidity": humidity}

    def test_default(self) -> None:
        # 1.25 + 2.3*2 + (2.3*2 + 0.575) + (2.3*2 + 0.575)
        self.assertAlmostEqual(measurement_time_ms(self.settings(2, 2, 2)), 16.2)

    def test_x1(self) -> None:
        self.assertAlmostEqual(measurement_time_ms(self.settings(1, 1, 1)), 9.3)

    def test_register_value_is_not_the_factor(self) -> None:
        # register value 5 stands for x16, so the measurement takes
        # about 113 ms (not the 37 ms a factor of 5 would give)
        self.assertAlmostEqual(measurement_time_ms(self.settings(5, 5, 5)), 112.8)
        # register value 3 stands for x4
        self.assertAlmostEqual(
            measurement_time_ms(self.settings(3, 3, 3)), 1.25 + 9.2 + 2 * (9.2 + 0.575)
        )

    def test_skipped_measurements(self) -> None:
        self.assertAlmostEqual(measurement_time_ms(self.settings(0, 0, 0)), 1.25)
        self.assertAlmostEqual(measurement_time_ms(self.settings(2, 2, 0)), 11.025)
        self.assertAlmostEqual(measurement_time_ms(self.settings(2, 0, 2)), 11.025)


class TestReadRawSensorWithCalibration(TestCase):
    def test_calibration_is_not_read_again(self) -> None:
        bus = FakeRecordingBus()
        calibration = [[1], [2], [3]]
        cals, data = read_raw_sensor(
            bus=bus,
            address=0xFFFFF,
            oversampling={"temperature": 2, "pressure": 2, "humidity": 2},
            reg_data=0xEEEEE,
            calibration=calibration,
        )
        self.assertIs(cals, calibration)
        self.assertEqual(data, 3)
        self.assertEqual(
            [command[:4] for command in bus.commands],
            [
                ["write_byte_data", 0xFFFFF, 0xF2, 2],
                ["write_byte_data", 0xFFFFF, 0xF4, 73],
                ["read_i2c_block_data", 0xFFFFF, 0xEEEEE, 8],
            ],
        )

    def test_waits_for_the_measurement(self) -> None:
        settings = {"temperature": 5, "pressure": 5, "humidity": 5}
        with mock.patch("bme280pi.readout.time.sleep") as fake_sleep:
            read_raw_sensor(
                bus=FakeRecordingBus(),
                address=0xFFFFF,
                oversampling=settings,
                reg_data=0xEEEEE,
            )
        fake_sleep.assert_called_once_with(measurement_time_ms(settings) / 1000)


def get_reference_calibration_data() -> list[list[int]]:
    return [
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
    ]


class TestGetModified(TestCase):
    def test(self) -> None:
        cals = get_reference_calibration_data()

        self.assertEqual(get_modified(cals, 3, get_character), 268)
        self.assertEqual(get_modified(cals, 3, get_unsigned_character), 268)
        self.assertEqual(get_modified(cals, 5, get_unsigned_character, shift=True), 50)


class TestProcessCalibration(TestCase):
    def test(self) -> None:
        cals = get_reference_calibration_data()

        correct_dig_t = [28256, 26827, 50]
        correct_dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230, 4285]
        correct_dig_h = [75, 385, 0, 268, 50, 30]

        dig_t, dig_p, dig_h = process_calibration_data(cals)

        # check temperature readings
        for i, dig_t_i in enumerate(dig_t):
            self.assertLess(abs(correct_dig_t[i] - dig_t_i), 1e-4)

        # check pressure readings
        for i, dig_p_i in enumerate(dig_p):
            self.assertLess(abs(correct_dig_p[i] - dig_p_i), 1e-4)

        # check humidity readings
        for i, dig_h_i in enumerate(dig_h):
            self.assertLess(abs(correct_dig_h[i] - dig_h_i), 1e-4)


class TestExtractRawValues(TestCase):
    def test(self) -> None:
        data = [76, 60, 0, 129, 49, 128, 94, 110]
        raw_pressure, raw_temperature, raw_humidity = extract_raw_values(data)
        self.assertEqual(raw_pressure, 312256)
        self.assertEqual(raw_temperature, 529176)
        self.assertEqual(raw_humidity, 24174)


class TestImproveTemperatureMeasurements(TestCase):
    def test(self) -> None:
        temp_raw = 529168
        dig_t = [28256, 26827, 50]
        temperature, t_fine = improve_temperature_measurement(temp_raw, dig_t)
        self.assertLess(abs(temperature - 2465), 1e-4)
        self.assertEqual(t_fine, 126213)


class TestImprovePressureMeasurements(TestCase):
    def test(self) -> None:
        # normal case
        raw_pressure = 312272
        dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230, 4285]
        t_fine = 126240
        pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
        self.assertLess(abs(pressure - 96909.62784910419), 1e-4)

    def test_special_case(self) -> None:
        # special case (var1 = 0)
        raw_pressure = 312272
        dig_p = [0, 6034, -2009, -3141, 8460, 523, -7938, 6421, -4430]
        t_fine = -146.81627832355957
        pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
        self.assertEqual(pressure, 0)


class TestHumidityMeasurements(TestCase):
    def test(self) -> None:
        raw_humidity = 24185
        dig_h = [75, 385, 0, 268, 50, 30]
        t_fine = 126200
        humidity = improve_humidity_measurement(raw_humidity, dig_h, t_fine)
        self.assertLess(abs(humidity - 41.07923074200165), 1e-4)


class TestExtractValues(TestCase):
    def test(self) -> None:
        data = [76, 59, 0, 129, 48, 0, 94, 121]
        dig_t = [28256, 26827, 50]
        dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230, 4285]
        dig_h = [75, 385, 0, 268, 50, 30]
        temp, pres, hum = extract_values(data, dig_t, dig_p, dig_h)

        self.assertLess(abs(temp - 2465.0), 1e-4)
        self.assertLess(abs(pres - 96913.34719558517), 1e-4)
        self.assertLess(abs(hum - 41.07923395171727), 1e-4)


class TestReadSensor(TestCase):
    def test(self) -> None:
        fake_data_bus = FakeDataBus(starting_point=0)
        correct_result = {
            "temperature": 24.65,
            "pressure": 969.1056565652227,
            "humidity": 41.07329061361983,
        }

        test_result = read_sensor(bus=fake_data_bus, address=0xFFFFF)

        for k in test_result:
            self.assertLess(abs(test_result[k] - correct_result[k]), 1e-4)

    def test_bad_inputs(self) -> None:
        fake_data_bus = FakeDataBus(0)
        with self.assertRaises(TypeError):
            read_sensor(
                bus=fake_data_bus,
                address=0xFFFFF,
                oversampling="some_string",  # type: ignore[arg-type]
            )
        with self.assertRaises(TypeError):
            read_sensor(bus=fake_data_bus, address=0xFFFF, oversampling=2)  # type: ignore[arg-type]
        with self.assertRaises(KeyError):
            read_sensor(
                bus=fake_data_bus, address=0xFFFF, oversampling={"something": 2}
            )

    def test_with_calibration(self) -> None:
        # the bus only provides the sensor data; the calibration is passed in
        fake_data_bus = FakeDataBus(starting_point=3)
        correct_result = {
            "temperature": 24.65,
            "pressure": 969.1056565652227,
            "humidity": 41.07329061361983,
        }

        test_result = read_sensor(
            bus=fake_data_bus,
            address=0xFFFFF,
            calibration=get_reference_calibration_data(),
        )

        for k in test_result:
            self.assertLess(abs(test_result[k] - correct_result[k]), 1e-4)

    def test_invalid_oversampling_values(self) -> None:
        fake_data_bus = FakeDataBus(0)
        with self.assertRaises(ValueError):
            read_sensor(
                bus=fake_data_bus,
                address=0xFFFF,
                oversampling={"temperature": 2, "pressure": 6, "humidity": 2},
            )


class TestValidateOversampling(TestCase):
    def test_default(self) -> None:
        self.assertEqual(
            validate_oversampling(None),
            {"temperature": 2, "pressure": 2, "humidity": 2},
        )

    def test_valid(self) -> None:
        for value in range(6):
            settings = {"temperature": value, "pressure": 5 - value, "humidity": 1}
            self.assertEqual(validate_oversampling(settings), settings)

    def test_not_a_dictionary(self) -> None:
        for value in ["some_string", 2, [2, 2, 2]]:
            with self.assertRaises(TypeError):
                validate_oversampling(value)  # type: ignore[arg-type]

    def test_missing_key(self) -> None:
        with self.assertRaisesRegex(KeyError, "humidity"):
            validate_oversampling({"temperature": 2, "pressure": 2})

    def test_unknown_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "humdity"):
            validate_oversampling(
                {"temperature": 2, "pressure": 2, "humidity": 2, "humdity": 2}
            )

    def test_out_of_range(self) -> None:
        for bad_value in [-1, 6, 16]:
            with self.assertRaisesRegex(ValueError, "pressure"):
                validate_oversampling(
                    {"temperature": 2, "pressure": bad_value, "humidity": 2}
                )

    def test_wrong_value_type(self) -> None:
        for bad_value in [2.0, "2", True, None]:
            with self.assertRaises(TypeError):
                validate_oversampling(
                    {"temperature": bad_value, "pressure": 2, "humidity": 2}  # type: ignore[dict-item]
                )
