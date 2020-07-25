"""Sensor class module.

This module contains the `Sensor` class, which can be used to read out the
BME280 sensor. The class provides a simple and intuitive interface, with
the main functions being `get_temperature`, `get_pressure`, and `get_humidity`.
Note that you can also get all this data at once with `get_data`, which returns
a dictionary with the three values.

For more information about how to use the `Sensor` class, have a look at the
documentation of the `Sensor` class itself.
"""

import smbus

from bme280pi.physics import calculate_abs_humidity, convert_pressure, \
    convert_temperature, round_to_n_significant_digits, pressure_at_sea_level
from bme280pi.raspberry_pi_version import detect_raspberry_pi_version
from bme280pi.readout import read_sensor


class I2CException(Exception):
    """Exception related to I2C (Inter-Integrated Circuit).

    Exception that is raised when an issue is encountered in the I2C
    section of the code. This is due to the I2C interface not being
    properly configured.
    """
    pass


class Sensor:
    """Sensor class.

    This class initializes the BME280 sensor, and offers an intuitive
    interface to access the sensor information. You can read out the
    temperature, humidity, and pressure using the corresponding get_
    commands:
        - `get_temperature`: get the current temperature
        - `get_pressure`: get the current pressure
        - `get_humidity`: get the current humidity

    The functions each support the `unit` argument, so you can specify the
    unit you would like the value to be in. For instance, the `get_temperature`
    function supports degrees C, F, or K.

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
    def __init__(self, address=0x76):
        """Initialize the sensor class.

        Carries out the following steps to initialize the class:
        - detect the Raspberry Pi version
        - initialize the bus
        - store information about the sensor in the class

        Args:
            address (int): the address of the sensor. default: 0x76
        """
        self.address = address
        self.bus = self._initialize_bus()

        self.chip_id, self.chip_version = self._get_info_about_sensor()

    def get_temperature(self, unit='C'):
        """Get a temperature reading.

        Fetches a temperature reading from the sensor and returns it in the
        user-specified temperature unit (degrees Celsius by default).
        The value can be returned in degrees Celsius (`unit='C'`),
        in degrees Fahrenheit (`unit='F'`), or in Kelvin (`unit='K'`).

        Args:
            unit (str): the unit the temperature should be in (C/F/K)

        Returns:
            float: the current temperature in the specified unit
        """
        data = self.get_data()
        return convert_temperature(data['temperature'], unit=unit)

    def get_humidity(self, relative=True):
        """Get a humidity reading.

        Fetches a humidity reading from the sensor. The value can be the
        relative humidity (`relative=True`), with values between 0 and 100.
        Alternatively, it returns the absolute humidity in kg / m^3.

        Args:
            relative (bool): indicate relative (instead of absolute) humidity

        Returns:
            float: the current relative/absolute humidity
        """
        data = self.get_data()

        if relative:
            return data['humidity']

        return calculate_abs_humidity(pressure=data['pressure'],
                                      temperature=data['temperature'],
                                      rel_humidity=data['humidity'])

    def get_pressure(self, unit='hPa', height_above_sea_level=None,
                     as_pressure_at_sea_level=False):
        """Get a pressure reading.

        Fetch the pressure from the sensor.
        The value can be returned in hPa (`unit='hPa'), Pa (`unit='Pa'),
        kPa (`unit='kPa'`), atm (`unit='atm'`), or mm Hg (`unit='mmHg'`).

        For meteorological applications, it can be useful to conver the
        pressure into its equivalent value at sea level. If you prefer this
        convention, set `as_pressure_at_sea_level=True`.
        In that case, you need to specify the height above sea level as well.

        Args:
            unit (str): unit the pressure should be in (Pa/hPa/kPa/atm/mmHg)
            height_above_sea_level (int/float): height above sea level in m
            as_pressure_at_sea_level (bool): quote as pressure above sea level

        Returns:
            float: the pressure in the specified unit, at sea level if desired
        """
        data = self.get_data()

        if as_pressure_at_sea_level:
            if height_above_sea_level is None:
                raise ValueError("You need to indicate the height above sea " +
                                 "level to get the equivalent value at sea " +
                                 "level.")
            data['pressure'] = pressure_at_sea_level(data['pressure'],
                                                     data['temperature'],
                                                     height_above_sea_level)
        return convert_pressure(data['pressure'], unit=unit)

    def get_data(self):
        """Get a reading from the sensor.

        Fetches the latest humidity, temperature, and pressure data
        from the sensor. The data is returned as a dictionary with
        keys "temperature", "humidity", and "pressure".

        Returns:
            dict: dictionary with current temperature, humidity, and pressure
        """
        return read_sensor(bus=self.bus,
                           address=self.address)

    def print_data(self, temp_unit='C', relative_humidity=True,
                   pressure_unit='hPa', n_significant_digits=4):
        """Print sensor data.

        Prints the temperature, humidity, and pressure in a easy readable
        format. The user can specify the temperature unit (e.g. "C") via
        `temp_unit`, the pressure unit (e.g. "hPa") via `pressure_unit`,
        and whether to use absolute or relative humidity via
        `relative_humidity`.

        Args:
            temp_unit (str): the unit the temperature should be in (C/F/K)
            relative_humidity (bool): relative instead of absolute humidity
            pressure_unit (str): pressure unit (Pa/hPa/kPa/atm/mmHg)
            n_significant_digits (int): number of significant digits for values

        Returns:
            None: values are printed, not returned.
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
        """Initialize the bus.

        Detects the raspberry pi version and initializes the bus.
        Note that the Raspberry Pi version detection is necessary because
        the first revisions needs to be initialized slightly differently.

        Returns:
            object: the bus to read data from
        """
        bus = None
        argument = 1
        if detect_raspberry_pi_version() in ['Model B R1',
                                             'Model A',
                                             'Model B+',
                                             'Model A+']:
            argument = 0

        try:
            bus = smbus.SMBus(argument)
        except FileNotFoundError:
            raise I2CException("SMBus raised a FileNotFoundError; this is " +
                               "usually due to the i2c interface being " +
                               "unconfigured. Please run 'sudo raspi-config'" +
                               " and select Interfacing Options -> I2C, " +
                               "choose and hit Enter, and then reboot. I2C " +
                               "should then be configured, and you should " +
                               "no longer see this exception")

        return bus

    def _get_info_about_sensor(self):
        """Fetch information about the sensor.

        Obtains the chip ID and version from sensor.

        Returns:
            tuple: chip ID and version as one string each
        """
        reg_id = 0xD0
        chip_id, chip_version = self.bus.read_i2c_block_data(self.address,
                                                             reg_id,
                                                             2)
        return chip_id, chip_version
