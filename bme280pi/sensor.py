"""
Sensor class module

You can use the Sensor class to access the BME280 sensor,
and obtain information through `get_temperature`,
`get_pressure`, and `get_humidity`. Note that you can also
get all at once with `get_data`.
"""

import smbus

from bme280pi.physics import calculate_abs_humidity, convert_pressure, \
    convert_temperature, round_to_n_significant_digits
from bme280pi.raspberry_pi_version import detect_raspberry_pi_version
from bme280pi.readout import read_sensor


class Sensor:
    """
    Sensor class

    This class initializes the BME280 sensor, and offers an intuitive
    interface to access the sensor information. You can read out the
    temperature, humidity, and pressure using the corresponding get_
    commands. You can also request the values in different units,
    e.g. temperature in C, F, or K.

    You can also use `print_data()` for a nicer presentation.

    Example usage:
    >>> sensor = Sensor()
    >>> sensor.get_temperature(unit='C')
    >>> sensor.get_temperature(unit='K')
    >>> sensor.get_humidity(relative=True)
    >>> sensor.get_humidity(relative=True)
    >>> sensor.get_pressure(unit='hPa')
    >>> sensor.get_pressure(unit='mmHg')
    """
    def __init__(self):
        """
        Initialize the sensor class:
        - detect the Raspberry Pi version
        - initialize the bus
        - store information about the sensor in the class
        """
        self.device_id = 0x76
        self.bus = self._initialize_bus()

        self.chip_id, self.chip_version = self._get_info_about_sensor()

    def get_temperature(self, unit='C'):
        """
        Fetch the temperature from the sensor.
        The value can be returned in degrees Celsius (`unit='C'`),
        in degrees Fahrenheit (`unit='K'`), or in Kelvin (`unit='K'`).
        """
        data = self.get_data()
        return convert_temperature(data['temperature'], unit=unit)

    def get_humidity(self, relative=True):
        """
        Fetch the humidity from the sensor.
        The value can be the relative humidity (`relative=True`), with
        values between 0 and 100. Alternatively, it returns the absolute
        humidity in kg / m^3.
        """
        data = self.get_data()

        if relative:
            return data['humidity']

        return calculate_abs_humidity(pressure=data['pressure'],
                                      temperature=data['temperature'],
                                      rel_humidity=data['humidity'])

    def get_pressure(self, unit='hPa'):
        """
        Fetch the pressure from the sensor.
        The value can be returned in hPa (`unit='hPa'), Pa (`unit='Pa'),
        kPa (`unit='kPa'`), atm (`unit='atm'`), or mm Hg (`unit='mmHg'`).
        """
        data = self.get_data()

        return convert_pressure(data['pressure'], unit=unit)

    def get_data(self):
        """
        Fetches the latest humidity, temperature, and pressure data
        from the sensor.
        """
        return read_sensor(bus=self.bus,
                           address=self.device_id)

    def print_data(self, temp_unit='C', relative_humidity=True,
                   pressure_unit='hPa', n_significant_digits=4):
        """
        Print sensor data
        """
        data = self.get_data()
        temperature = convert_temperature(data['temperature'], temp_unit)
        pressure = convert_pressure(data['pressure'], pressure_unit)
        humidity = data['humidity']
        humidity_unit = '%'
        if not relative_humidity:
            humidity = calculate_abs_humidity(pressure=data['pressure'],
                                              temperature=data['temperature'],
                                              rel_humidity=data['humidity'])
            humidity_unit = "kg / m^3"

        # round to n significant digits
        temperature = round_to_n_significant_digits(temperature,
                                                    n_significant_digits)
        humidity = round_to_n_significant_digits(humidity,
                                                 n_significant_digits)
        pressure = round_to_n_significant_digits(pressure,
                                                 n_significant_digits)
        print("Temperature: ", temperature, temp_unit)
        print("Humidity:    ", humidity, humidity_unit)
        print("Pressure:    ", pressure, pressure_unit)

    @staticmethod
    def _initialize_bus():
        """
        Detect the raspberry pi version and initialize the bus
        Note that the Raspberry Pi version detection is necessary because
        the first revisions needs to be initialized slightly differently.
        """
        bus = None
        if detect_raspberry_pi_version() in ['Model B R1',
                                             'Model A',
                                             'Model B+',
                                             'Model A+']:
            bus = smbus.SMBus(0)
        else:
            bus = smbus.SMBus(1)

        return bus

    def _get_info_about_sensor(self):
        """
        Obtain chip ID and version from sensor
        """
        reg_id = 0xD0
        chip_id, chip_version = self.bus.read_i2c_block_data(self.device_id,
                                                             reg_id,
                                                             2)
        return chip_id, chip_version
