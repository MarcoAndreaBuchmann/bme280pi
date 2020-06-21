import unittest

from bme280pi.readout import (get_short, get_unsigned_short, get_character,
                              get_unsigned_character, read_raw_sensor,
                              get_modified, process_calibration_data,
                              extract_raw_values,
                              improve_temperature_measurement,
                              improve_pressure_measurement,
                              improve_humidity_measurement, extract_values,
                              read_sensor)


class FakeBus:
    """
    This is a fake bus class (to simulate SMBus for tests)
    This class records all commands.
    """
    def __init__(self):
        """
        Initialize a fake bus class
        """
        self.commands = []

    def write_byte_data(self, address, register, value, force=None):
        self.commands.append(['write_byte_data', address, register,
                              value, force])

    def read_i2c_block_data(self, address, register, length, force=None):
        self.commands.append(['read_i2c_block_data', address, register,
                              length, force])
        return len(self.commands)


class test_get_short(unittest.TestCase):
    def test(self):
        test_result = get_short(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result - 385), 1e-6)


class test_get_unsigned_short(unittest.TestCase):
    def test(self):
        test_result = get_unsigned_short(data=[129, 1, 0, 16, 44, 3, 30],
                                         index=0)
        self.assertLess(abs(test_result - 385), 1e-6)


class test_get_character(unittest.TestCase):
    def test(self):
        test_result = get_character(data=[129, 1, 0, 16, 44, 3, 30], index=0)
        self.assertLess(abs(test_result + 127), 1e-6)


class test_get_unsigned_character(unittest.TestCase):
    def test(self):
        test_result = get_unsigned_character(data=[129, 1, 0, 16, 44, 3, 30],
                                             index=0)
        self.assertLess(abs(test_result - 129), 1e-6)


class test_read_raw_sensor(unittest.TestCase):
    def test(self):
        bus = FakeBus()
        cals, data = read_raw_sensor(bus=bus,
                                     address="address",
                                     oversampling={'temperature': 2,
                                                   'pressure': 2,
                                                   'humidity': 2},
                                     mode=1,
                                     reg_data="reg_data")
        self.assertEqual(cals[0], 3)
        self.assertEqual(cals[1], 4)
        self.assertEqual(cals[2], 5)
        self.assertEqual(data, 6)

        correct_commands = [['write_byte_data', 'address', 242, 2, None],
                            ['write_byte_data', 'address', 244, 73, None],
                            ['read_i2c_block_data', 'address', 136, 24, None],
                            ['read_i2c_block_data', 'address', 161, 1, None],
                            ['read_i2c_block_data', 'address', 225, 7, None],
                            ['read_i2c_block_data', 'address', 'reg_data', 8,
                             None]]

        for i in range(len(correct_commands)):
            # check type of command
            self.assertEqual(bus.commands[i][0], correct_commands[i][0])
            # check address
            self.assertEqual(bus.commands[i][1], correct_commands[i][1])
            # check register
            self.assertEqual(bus.commands[i][2], correct_commands[i][2])
            # check length or value
            self.assertEqual(bus.commands[i][3], correct_commands[i][3])
            # check whether force was set
            self.assertEqual(bus.commands[i][4], correct_commands[i][4])


class test_get_modified(unittest.TestCase):
    def test(self):
        cals = ([96, 110, 203, 104, 50, 0, 29, 145, 59, 215, 208, 11, 232, 38,
                 42, 255, 249, 255, 172, 38, 10, 216, 189, 16],
                [75],
                [129, 1, 0, 16, 44, 3, 30])

        self.assertEqual(get_modified(cals, 3, get_character), 268)
        self.assertEqual(get_modified(cals, 3, get_unsigned_character), 268)
        self.assertEqual(get_modified(cals, 5, get_unsigned_character,
                                      shift=True),
                         50)


class test_process_calibration_data(unittest.TestCase):
    def test(self):
        cals = ([96, 110, 203, 104, 50, 0, 29, 145, 59, 215, 208, 11, 232, 38,
                 42, 255, 249, 255, 172, 38, 10, 216, 189, 16],
                [75],
                [129, 1, 0, 16, 44, 3, 30])

        correct_dig_t = [28256, 26827, 50]
        correct_dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230,
                         4285]
        correct_dig_h = [75, 385, 0, 268, 50, 30]

        dig_t, dig_p, dig_h = process_calibration_data(cals)

        # check temperature readings
        for i in range(len(dig_t)):
            self.assertLess(abs(correct_dig_t[i] - dig_t[i]), 1e-4)

        # check pressure readings
        for i in range(len(dig_p)):
            self.assertLess(abs(correct_dig_p[i] - dig_p[i]), 1e-4)

        # check humidity readings
        for i in range(len(dig_h)):
            self.assertLess(abs(correct_dig_h[i] - dig_h[i]), 1e-4)


class test_extract_raw_values(unittest.TestCase):
    def test(self):
        data = [76, 60, 0, 129, 49, 128, 94, 110]
        raw_pressure, raw_temperature, raw_humidity = extract_raw_values(data)
        self.assertEqual(raw_pressure, 312256)
        self.assertEqual(raw_temperature, 529176)
        self.assertEqual(raw_humidity, 24174)


class test_improve_temperature_measurement(unittest.TestCase):
    def test(self):
        temp_raw = 529168
        dig_t = [28256, 26827, 50]
        temperature, t_fine = improve_temperature_measurement(temp_raw, dig_t)
        self.assertLess(abs(temperature - 2465), 1e-4)
        self.assertEqual(t_fine, 126213)


class test_improve_pressure_measurement(unittest.TestCase):
    def test(self):
        # normal case
        raw_pressure = 312272
        dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230, 4285]
        t_fine = 126240
        pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
        self.assertLess(abs(pressure - 96909.62784910419), 1e-4)

        # special case (var1 = 0)
        raw_pressure = 312272
        dig_p = [0, 6034, -2009, -3141, 8460, 523, -7938, 6421, -4430]
        t_fine = -146.81627832355957
        pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
        self.assertEqual(pressure, 0)


class test_improve_humidity_measurement(unittest.TestCase):
    def test(self):
        raw_humidity = 24185
        dig_h = [75, 385, 0, 268, 50, 30]
        t_fine = 126200
        humidity = improve_humidity_measurement(raw_humidity, dig_h, t_fine)
        self.assertLess(abs(humidity - 41.07923074200165), 1e-4)


class test_extract_values(unittest.TestCase):
    def test(self):
        data = [76, 59, 0, 129, 48, 0, 94, 121]
        dig_t = [28256, 26827, 50]
        dig_p = [37149, -10437, 3024, 9960, -214, -7, 9900, -10230, 4285]
        dig_h = [75, 385, 0, 268, 50, 30]
        t, p, h = extract_values(data, dig_t, dig_p, dig_h)

        self.assertLess(abs(t - 2465.0), 1e-4)
        self.assertLess(abs(p - 96913.34719558517), 1e-4)
        self.assertLess(abs(h - 41.07923395171727), 1e-4)


class FakeDataBus:
    def __init__(self):
        self.i_read = -1
        self.data = [[96, 110, 203, 104, 50, 0, 29, 145, 59, 215, 208, 11,
                      232, 38, 42, 255, 249, 255, 172, 38, 10, 216, 189, 16],
                     [75],
                     [129, 1, 0, 16, 44, 3, 30],
                     [76, 60, 128, 129, 49, 128, 94, 120]]

    def write_byte_data(self, address, register, value, force=None):
        pass

    def read_i2c_block_data(self, address, register, length, force=None):
        self.i_read += 1
        return self.data[self.i_read]


class test_read_sensor(unittest.TestCase):
    def test(self):
        fake_data_bus = FakeDataBus()
        correct_result = {'temperature': 24.65,
                          'pressure': 969.1056565652227,
                          'humidity': 41.07329061361983}

        test_result = read_sensor(bus=fake_data_bus,
                                  address="fake_address")

        for k in test_result:
            self.assertLess(abs(test_result[k] - correct_result[k]),
                            1e-4)
