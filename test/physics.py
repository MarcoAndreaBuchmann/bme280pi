from unittest import TestCase

from bme280pi.physics import (validate_pressure, validate_temperature,
                              validate_humidity, pressure_function,
                              calculate_abs_humidity, convert_pressure,
                              convert_temperature,
                              round_to_n_significant_digits)


class TestValidation(TestCase):
    def test_validate_pressure(self):
        with self.assertRaises(TypeError):
            validate_pressure("string_input")
        with self.assertRaises(ValueError):
            validate_pressure(-1)
        with self.assertRaises(ValueError):
            validate_pressure(1200)

    def test_validate_temperature(self):
        with self.assertRaises(TypeError):
            validate_temperature("string_input")
        with self.assertRaises(ValueError):
            validate_temperature(-111)
        with self.assertRaises(ValueError):
            validate_temperature(111)

    def test_validate_humidity(self):
        with self.assertRaises(TypeError):
            validate_humidity("string_input")
        with self.assertRaises(ValueError):
            validate_humidity(-1)
        with self.assertRaises(ValueError):
            validate_humidity(123)


class TestPressureFunction(TestCase):
    def test(self):
        test_values = [100, 800, 850, 900, 950, 1000, 1050, 1100]
        correct_values = [1.001176,
                          1.0040355,
                          1.0041989411764707,
                          1.0043617777777778,
                          1.004524105263158,
                          1.0046860000000002,
                          1.0048475238095238,
                          1.0050087272727273]

        for i_test, test_value in enumerate(test_values):
            test_result = pressure_function(test_value)
            correct_result = correct_values[i_test]
            self.assertLess(abs(test_result - correct_result), 1e-6)

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            pressure_function(0)
        with self.assertRaises(ValueError):
            pressure_function(1111)
        with self.assertRaises(TypeError):
            pressure_function('a')


class TestCalculateAbsHumidity(TestCase):
    def test(self):
        test_pressure = [100, 800, 850, 900, 950, 1000, 1050, 1100]
        test_temp = [-10, 0, 10, 15, 20, 25, 40, 60]
        test_rel = [80, 10, 20, 90, 40, 50, 43.25, 12.34]

        correct_values = [0.0018930155819513275,
                          0.00048681001461818693,
                          0.0018843546921809028,
                          0.011566932891098143,
                          0.006927846890531939,
                          0.011536889704637605,
                          0.022155411985739303,
                          0.01612715205125449]

        for i_test, correct_value in enumerate(correct_values):
            result = calculate_abs_humidity(pressure=test_pressure[i_test],
                                            temperature=test_temp[i_test],
                                            rel_humidity=test_rel[i_test])
            self.assertLess(abs(result - correct_value), 1e-6)

    def test_valid_range(self):
        with self.assertRaises(ValueError):
            # pressure too low
            calculate_abs_humidity(pressure=0,
                                   temperature=25,
                                   rel_humidity=50)
        with self.assertRaises(ValueError):
            # pressure too high
            calculate_abs_humidity(pressure=1111,
                                   temperature=25,
                                   rel_humidity=50)
        with self.assertRaises(ValueError):
            # rel humidity too low
            calculate_abs_humidity(pressure=975,
                                   temperature=25,
                                   rel_humidity=-1)
        with self.assertRaises(ValueError):
            # rel humidity too high
            calculate_abs_humidity(pressure=975,
                                   temperature=25,
                                   rel_humidity=110)
        with self.assertRaises(ValueError):
            # temp too low
            calculate_abs_humidity(pressure=975,
                                   temperature=-101,
                                   rel_humidity=50)
        with self.assertRaises(ValueError):
            # temp too high
            calculate_abs_humidity(pressure=975,
                                   temperature=101,
                                   rel_humidity=50)

    def test_bad_arguments(self):
        with self.assertRaises(TypeError):
            calculate_abs_humidity(pressure='a',
                                   temperature=25,
                                   rel_humidity=110)
        with self.assertRaises(TypeError):
            calculate_abs_humidity(pressure=975,
                                   temperature='a',
                                   rel_humidity=110)
        with self.assertRaises(TypeError):
            calculate_abs_humidity(pressure=975,
                                   temperature=25,
                                   rel_humidity='a')


class TestConvertPressure(TestCase):
    def test(self):
        test_values = [100, 500, 850, 900, 950, 1000, 1050, 1099]

        correct_values = {'hPa': test_values,
                          'Pa': [100 * p for p in test_values],
                          'kPa': [0.1 * p for p in test_values],
                          'atm': [9.8692316931427E-4 * p for p in test_values],
                          'mmHg': [0.750062 * p for p in test_values]}

        for unit in correct_values:
            for i in range(len(correct_values[unit])):
                self.assertLess(abs(correct_values[unit][i] -
                                    convert_pressure(test_values[i],
                                                     unit=unit)),
                                1e-6)

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            convert_pressure(-123)
        with self.assertRaises(ValueError):
            convert_pressure(1234)

        with self.assertRaises(TypeError):
            convert_pressure('a')
        with self.assertRaises(Exception):
            convert_pressure(123, 'UnknownUnit')


class TestConvertTemperature(TestCase):
    def test(self):
        test_values = [-50, -40, 30, 20, 10, 0, 12.34, 20, 30, 40, 50, 99]

        correct_values = {'C': test_values,
                          'F': [32 + (9. / 5) * t for t in test_values],
                          'K': [273.15 + t for t in test_values]}

        for unit in correct_values:
            for i in range(len(correct_values[unit])):
                self.assertLess(abs(correct_values[unit][i] -
                                    convert_temperature(test_values[i],
                                                        unit=unit)),
                                1e-6)

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            convert_temperature(-123)
        with self.assertRaises(ValueError):
            convert_temperature(123)

        with self.assertRaises(TypeError):
            convert_temperature('a')
        with self.assertRaises(Exception):
            convert_temperature(23, 'UnknownUnit')


class TestRoundToNSignificantDigits(TestCase):
    def test(self):
        multipliers = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
        test_values = [1.23456789 * m for m in multipliers]

        correct_results = {1: [1 * m for m in multipliers],
                           2: [1.2 * m for m in multipliers],
                           3: [1.23 * m for m in multipliers],
                           4: [1.235 * m for m in multipliers],
                           5: [1.2346 * m for m in multipliers]}

        for n_digits in correct_results:
            for i, test_value in enumerate(test_values):
                test_result = round_to_n_significant_digits(test_value,
                                                            n_digits)
                self.assertLess(abs(correct_results[n_digits][i] -
                                    test_result),
                                1e-6)

    def test_exceptions(self):
        with self.assertRaises(TypeError):
            round_to_n_significant_digits('a', 2)
        with self.assertRaises(TypeError):
            round_to_n_significant_digits(2, 'a')
        with self.assertRaises(ValueError):
            round_to_n_significant_digits(2, 0)
        with self.assertRaises(ValueError):
            round_to_n_significant_digits(2, -1)
        with self.assertRaises(TypeError):
            round_to_n_significant_digits(2, 1.234)
