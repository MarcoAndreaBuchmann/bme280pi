"""

Functions to read out the raw sensor data and processes it to obtain
sensible values

This module is based on the bme280 script from MattHawkinsUK,
https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/bme280.py

"""

import time
from ctypes import c_short


def get_short(data, index):
    """
    return two bytes from data as a signed 16-bit value
    """
    return c_short((data[index+1] << 8) + data[index]).value


def get_unsigned_short(data, index):
    """
    return two bytes from data as an unsigned 16-bit value
    """
    return (data[index+1] << 8) + data[index]


def get_character(data, index):
    """
    return one byte from data as a signed char
    """
    result = data[index]
    if result > 127:
        result -= 256
    return result


def get_unsigned_character(data, index):
    """
    return one byte from data as an unsigned char
    """
    result = data[index] & 0xFF
    return result


def read_raw_sensor(bus, address, oversampling, mode, reg_data):
    """
    Read out the raw sensor data
    """
    # Oversample setting for humidity register - page 26
    reg_control = 0xF4
    reg_control_hum = 0xF2
    bus.write_byte_data(address, reg_control_hum, oversampling['humidity'])

    control1 = oversampling['temperature'] << 5
    control = control1 | oversampling['pressure'] << 2 | mode
    bus.write_byte_data(address, reg_control, control)

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
    """
    Extract information from block, and shifts it
    if necessary
    """
    dig = get_character(cal[2], i)
    dig = (dig << 24) >> 20
    if shift:
        return dig | (function(cal[2], 4) >> 4 & 0x0F)
    return dig | (function(cal[2], 4) & 0x0F)


def process_calibration_data(cal):
    """
    Process calibration data to extract the information pertaining
    to temperature, pressure, and humidity
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


def extract_raw_values(data):
    """
    extract raw reading of temperature, pressure, and humidity
    """
    raw_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    raw_temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    raw_humidity = (data[6] << 8) | data[7]

    return raw_pressure, raw_temperature, raw_humidity


def improve_temperature_measurement(temp_raw, dig_t):
    """
    Refine the temperature measurement
    """
    var1 = ((((temp_raw >> 3) - (dig_t[0] << 1))) * (dig_t[1])) >> 11
    var2 = (((temp_raw >> 4) - (dig_t[0])) * ((temp_raw >> 4) - (dig_t[0])))
    var3 = ((var2 >> 12) * (dig_t[2])) >> 14
    t_fine = var1 + var3
    temperature = float(((t_fine * 5) + 128) >> 8)
    return temperature, t_fine


def improve_pressure_measurement(raw_pressure, dig_p, t_fine):
    """
    Refine the pressure measurement and adjust it for the
    available temperature information, along with the pressure
    readout details
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
    """
    Refine humidity measurement by using the available temperature
    information, along with the humidity readout details
    """
    humidity = t_fine - 76800.0
    term1 = raw_humidity - (dig_h[3] * 64.0 + dig_h[4] / 16384.0 * humidity)
    term2a = humidity * (1.0 + dig_h[2] / 67108864.0 * humidity)
    term2 = dig_h[1] / 65536.0 * (1.0 + dig_h[5] / 67108864.0 * term2a)
    humidity = term1 * term2
    humidity = humidity * (1.0 - dig_h[0] * humidity / 524288.0)
    humidity = max(0, min(humidity, 100))
    return humidity


def extract_values(data, dig_t, dig_p, dig_h):
    """
    Extract temperature, pressure, and humidity from raw data and
    correct it to provide the best measurement
    """
    raw_pressure, raw_temperature, raw_humidity = extract_raw_values(data)

    temperature, t_fine = improve_temperature_measurement(raw_temperature,
                                                          dig_t)
    pressure = improve_pressure_measurement(raw_pressure, dig_p, t_fine)
    humidity = improve_humidity_measurement(raw_humidity, dig_h, t_fine)

    return temperature, pressure, humidity


def read_sensor(bus, address, reg_data=0xF7, mode=1,
                oversampling={'temperature': 2,
                              'pressure': 2,
                              'humidity': 2}):
    """
    Read out the data from the sensor

    See the data sheet for more information, e.g. p27 for oversampling
    settings, App. B for measurement time, Sec. 4 for data readout, etc.

    This module is based on the bme280 script from MattHawkinsUK.
    """
    cal, data = read_raw_sensor(bus=bus,
                                address=address,
                                oversampling=oversampling,
                                mode=mode,
                                reg_data=reg_data)

    dig_t, dig_p, dig_h = process_calibration_data(cal)

    temperature, pressure, humidity = extract_values(data, dig_t, dig_p, dig_h)

    return {'temperature': temperature / 100.0,
            'pressure': pressure / 100.0,
            'humidity': humidity}
