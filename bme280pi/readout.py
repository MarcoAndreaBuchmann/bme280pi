"""Functions to read out and interpret the raw sensor data.

This module contains all functions necessary for reading out the raw data from
the BME280 sensor according to the Bosch data sheet, and processing this raw
data in order to obtain a more digestible format, i.e. the temperature,
pressure, and relative humidity.

The best way to use this module is through the `Sensor` class in `sensor.py`,
i.e. by initializing a `Sensor` object and using it to fetch data. One could
use the functions in this module to do the individual steps, but it's much
more practical to use the `Sensor` class directly and have it take care of
everything.

Example usage:
>>> sensor = Sensor()
>>> sensor.get_temperature(unit='C')

Have a look at the `Sensor` class in `sensor.py` for more detailed information.

The (helper) functions contained in this module are the following:
- get_short(data, index):
- get_unsigned_short(data, index):
- get_character(data, index):
- get_unsigned_character(data, index):
- read_raw_sensor(bus, address, oversampling, reg_data):
- get_modified(cal, i, function, shift=False):
- process_calibration_data(cal):
- shift_read(values, i, j, k):
- extract_raw_values(data):
- improve_temperature_measurement(temp_raw, dig_t):
- improve_pressure_measurement(raw_pressure, dig_p, t_fine):
- improve_humidity_measurement(raw_humidity, dig_h, t_fine):
- extract_values(data, dig_t, dig_p, dig_h):
- validate_oversampling(oversampling=None):
- read_sensor(bus, address, reg_data=0xF7,

Notes:
1) This module is based on the bme280 script from MattHawkinsUK,
https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/bme280.py

2) Before changing parameters in the code, it is recommended to have a look at
the data sheet available directly from Bosch:
https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/
"""

import time
from ctypes import c_short


def get_short(data, index):
    """Return two bytes from data as a signed 16-bit value.

    Args:
        data (list): raw data from sensor
        index (int): index entry from which to read data

    Returns:
        c_short: extracted signed 16-bit value
    """
    return c_short((data[index + 1] << 8) + data[index]).value


def get_unsigned_short(data, index):
    """Return two bytes from data as an unsigned 16-bit value.

    Args:
        data (list): raw data from sensor
        index (int): index entry from which to read data

    Returns:
        int: extracted unsigned 16-bit value
    """
    return (data[index + 1] << 8) + data[index]


def get_character(data, index):
    """Return one byte from data as a signed char.

    Args:
        data (list): raw data from sensor
        index (int): index entry from which to read data

    Returns:
        int: extracted signed char value
    """
    result = data[index]
    if result > 127:
        result -= 256
    return result


def get_unsigned_character(data, index):
    """Return one byte from data as an unsigned char.

    Args:
        data (list): raw data from sensor
        index (int): index entry from which to read data

    Returns:
        int: extracted unsigned 16-bit value
    """
    result = data[index] & 0xFF
    return result


def read_raw_sensor(bus, address, oversampling, reg_data):
    """Read raw sensor data.

    For an explanation of the parameter storage, naming, and
    data type, see Table 16, page 25, of the data sheet.
    For information about oversampling, see e.g. page 26.
    For a memory map, see Table 18 on page 27.

    Args:
        bus (object): bus from which to read data
        address (int): address at which to read data
        oversampling (dict): over-sampling rates (see data sheet)
        reg_data (int): register at which to obtain data

    Returns:
        tuple: calibration data as a list, and sensor data
    """
    control_register_address = 0xF4
    control_register_address_humidity = 0xF2
    bus.write_byte_data(address, control_register_address_humidity,
                        oversampling['humidity'])

    control1 = oversampling['temperature'] << 5
    control = control1 | oversampling['pressure'] << 2 | 1
    bus.write_byte_data(address, control_register_address, control)

    # Read blocks of calibration data from EEPROM
    # See Page 22 data sheet
    cal1 = bus.read_i2c_block_data(address, 0x88, 24)
    cal2 = bus.read_i2c_block_data(address, 0xA1, 1)
    cal3 = bus.read_i2c_block_data(address, 0xE1, 7)

    # Wait in ms
    # source: Datasheet Appendix B
    wait_time = 2.4 + 2.3 * sum(oversampling.values())

    # Wait the required time
    time.sleep(wait_time / 1000)

    # Read temperature/pressure/humidity
    data = bus.read_i2c_block_data(address, reg_data, 8)

    return (cal1, cal2, cal3), data


def get_modified(cal, i, function, shift=False):
    """Obtain and modify data from block.

    Extracts information from block, and shifts it
    if necessary.

    Args:
        cal (list): calibration data
        i (int): index from which to read
        function (object): function to apply to data
        shift (bool): whether to apply a shift to result

    Returns:
        int: processed data from specified blocks
    """
    dig = get_character(cal[2], i)
    dig = (dig << 24) >> 20
    if shift:
        return dig | (function(cal[2], 4) >> 4 & 0x0F)
    return dig | (function(cal[2], 4) & 0x0F)


def process_calibration_data(cal):
    """Process calibration data.

    Processes calibration data to extract the information pertaining
    to temperature, pressure, and humidity. Returns the relevant block
    data.

    Args:
        cal (list): calibration data

    Returns:
        tuple: block values for temperature, pressure, and humidity
    """
    dig_t = [get_unsigned_short(cal[0], 0),
             get_short(cal[0], 2),
             get_short(cal[0], 4)]

    dig_p = []
    for i in range(6, 23, 2):
        value = None
        if i == 6:
            value = get_unsigned_short(cal[0], i)
        else:
            value = get_short(cal[0], i)
        dig_p.append(value)

    dig_h = [get_unsigned_character(cal[1], 0),
             get_short(cal[2], 0),
             get_unsigned_character(cal[2], 2),
             get_modified(cal, 3, get_character),
             get_modified(cal, 5, get_unsigned_character, shift=True),
             get_character(cal[2], 6)
             ]

    return dig_t, dig_p, dig_h


def shift_read(values, i, j, k):
    """Read raw data from array and shift it.

    Reads values from array and shifts them the following way:
    - the first one is shifted to the left by 12 places
    - the second value is shifted to the left by 4 places
    - the third one is shifted to the right by 4 places
    Then a bitwise "or" operation is performed.
    Example: values = [1, 2, 3]
    - the first entry (1) is shifted 12 places to the left:
          000000000001 becomes 1000000000000
    - the second entry (2) is shifted 4 places to the left:
          000000000010 becomes 000000100000
    - the third entry (3) is shifted 4 places to the right:
          000000000011 becomes 000000000000
    Finally, a bit-wise "or" is performed:
          1000000000000 or
          0000000100000 or
          0000000000000 is
          1000000100000
    which, in decimal, is 4128.

    Args:
        values (list): the raw values
        i (int): first index to read from
        j (int): second index to read from
        k (int): third index to read from

    Returns:
        int: extracted (shifted) values
    """
    return (values[i] << 12) | (values[j] << 4) | (values[k] >> 4)


def extract_raw_values(data):
    """Extract raw reading of temperature, pressure, and humidity.

    Args:
        data (list): raw sensor data

    Returns:
        tuple: raw pressure, temperature, and humidity
    """
    raw_pressure = shift_read(data, 0, 1, 2)
    raw_temperature = shift_read(data, 3, 4, 5)
    raw_humidity = (data[6] << 8) | data[7]

    return raw_pressure, raw_temperature, raw_humidity


def improve_temperature_measurement(temp_raw, dig_t):
    """Refine the temperature measurement.

    Adapts the raw temperature measurement according to a formula specified
    in the Bosch data sheet.

    Args:
        temp_raw (int): raw temperature reading
        dig_t (list): blocks of data pertaining to temperature

    Returns:
        tuple: refined temperature measurement and reference point

    Reference:
        Bosch data sheet, Appendix A, "BME280_compensate_T_double"
    """
    var1 = ((((temp_raw >> 3) - (dig_t[0] << 1))) * (dig_t[1])) >> 11
    var2 = (((temp_raw >> 4) - (dig_t[0])) * ((temp_raw >> 4) - (dig_t[0])))
    var3 = ((var2 >> 12) * (dig_t[2])) >> 14
    t_fine = var1 + var3
    temperature = float(((t_fine * 5) + 128) >> 8)
    return temperature, t_fine


def improve_pressure_measurement(raw_pressure, dig_p, t_fine):
    """Refine the pressure measurement.

    Adapts the pressure measurement according to the formula specified in
    the Bosch data sheet, and adjust it for the available temperature
    measurement, along with the pressure readout details.

    Args:
        raw_pressure (float): raw temperature measurement
        dig_p (list): data blocks pertaining to pressure
        t_fine (float): temperature measurement

    Returns:
        float: improved pressure measurement

    Reference:
    Bosch data sheet, Appendix A, "BME280_compensate_P_double"
    """
    var1 = t_fine / 2.0 - 64000.0
    var2 = var1 * var1 * dig_p[5] / 32768.0
    var2 = var2 + var1 * dig_p[4] * 2.0
    var2 = var2 / 4.0 + dig_p[3] * 65536.0
    var1 = (dig_p[2] * var1 * var1 / 524288.0 + dig_p[1] * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * dig_p[0]

    if var1 == 0:
        pressure = 0
    else:
        pressure = 1048576.0 - raw_pressure
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = dig_p[8] * pressure * pressure / 2147483648.0
        var2 = pressure * dig_p[7] / 32768.0
        pressure = pressure + (var1 + var2 + dig_p[6]) / 16.0

    return pressure


def improve_humidity_measurement(raw_humidity, dig_h, t_fine):
    """Refine the humidity measurement.

    Adapts the humidity measurement by using the available temperature
    information, along with the humidity readout details.

    Args:
        raw_humidity (int): raw humidity
        dig_h (list): raw data blocks pertaining to humidity measurement
        t_fine (float): temperature measurement

    Returns:
        float: refined humidity measurement

    Reference:
    Bosch data sheet, Appendix A, "BME280_compensate_H_double"
    """
    base_value = t_fine - 76800.0
    term1 = raw_humidity - (dig_h[3] * 64.0 + dig_h[4] / 16384.0 * base_value)
    term2a = base_value * (1.0 + dig_h[2] / 67108864.0 * base_value)
    term2 = dig_h[1] / 65536.0 * (1.0 + dig_h[5] / 67108864.0 * term2a)
    humidity = term1 * term2
    humidity = humidity * (1.0 - dig_h[0] * humidity / 524288.0)
    humidity = max(0, min(humidity, 100))
    return humidity


def extract_values(data, dig_t, dig_p, dig_h):
    """Extract values from raw data.

    Extracts temperature, pressure, and humidity from raw data and
    correct it to provide the best measurement.

    Args:
        data (list): data blocks from sensor
        dig_t (list): data blocks pertaining to temperature measurement
        dig_p (list): data blocks pertaining to pressure measurement
        dig_h (list): data blocks pertaining to humidity measurement

    Returns:
        tuple: three floats representing temperature, pressure, and humidity
    """
    raw_pressure, raw_temperature, raw_humidity = extract_raw_values(data)

    temperature, t_fine = improve_temperature_measurement(raw_temperature,
                                                          dig_t)
    pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
    humidity = improve_humidity_measurement(raw_humidity, dig_h, t_fine)

    return temperature, pressure, humidity


def validate_oversampling(oversampling=None):
    """Validate the `oversampling` parameter.

    Checks whether the parameter is valid. This parameter can either be None
    (to use the default values) or it can be a dictionary containing the
    three keys "temperature", "humidity", and "pressure".

    Args:
        oversampling (dict): None or a dictionary with over-sampling values

    Returns:
        dict: oversampling values as a dictionary
    """
    if oversampling is None:
        oversampling = {'temperature': 2,
                        'pressure': 2,
                        'humidity': 2}

    if not isinstance(oversampling, dict):
        raise TypeError("oversampling must be a dictionary")

    return oversampling


def read_sensor(bus, address, reg_data=0xF7,
                oversampling=None):
    """Read measurements from sensor.

    Reads the raw information from the sensor and converts it into a
    readable format. The function returns a dictionary with the measurements,
    with the three keys "temperature",
    See the data sheet for more information, e.g. p27 for oversampling
    settings, App. B for measurement time, Sec. 4 for data readout, etc.

    If no oversampling is defined, the code defaults to the standard 2/2/2
    for temperature/humidity/pressure. If you wish to specify your own
    oversampling parameters, please pass a dictionary to `oversampling` with
    the keys 'temperature', 'pressure', and 'humidity'.

    This module is based on the bme280 script from MattHawkinsUK, which in
    turn is based on the data sheet from Bosch (see references below).

    Args:
        bus (object): the sensor bus to read from
        address (int): the address from which to read data
        reg_data (int): register at which to obtain data
        oversampling (dict): oversampling rates

    Returns:
         dict: measurements for temperature, pressure, and humidity

    References:
    https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/
    """
    oversampling = validate_oversampling(oversampling=oversampling)

    cal, data = read_raw_sensor(bus=bus,
                                address=address,
                                oversampling=oversampling,
                                reg_data=reg_data)

    dig_t, dig_p, dig_h = process_calibration_data(cal)

    temperature, pressure, humidity = extract_values(data, dig_t, dig_p, dig_h)

    return {'temperature': temperature / 100.0,
            'pressure': pressure / 100.0,
            'humidity': humidity}
