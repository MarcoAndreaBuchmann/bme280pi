"""
Physics functions for pressure/temperature/humidity/...

Provides functions related to converting humidity from relative
to absolute humidity. Also provides functions for converting
pressure & temperature into different units (e.g. Kelvin, mm Hg),
and to round numbers to a n significant digits.

source for formulae:
https://planetcalc.com/2167/
"""

import math


def validate_pressure(pressure):
    """
    Validates pressure:
    - needs to be positive
    - needs to be smaller than 1100 (largest value ever was 1083)

    Input:
    - pressure (in hPa)
    """
    if not isinstance(pressure, (float, int)):
        raise TypeError("Pressure must be int or float")

    if pressure <= 0 or pressure > 1100:
        raise ValueError("Pressure must be between 0 and 1100")


def validate_temperature(temperature):
    """
    Validates pressure:
    - needs to be smaller than 100 degrees (humidity calculations
      don't make much sense above this temperature)
    - needs to be larger than -100 (same reason)

    Input:
    - temperature (in C)
    """
    if not isinstance(temperature, (float, int)):
        raise TypeError("Temperature must be int or float")

    if temperature < -100 or temperature > 100:
        raise ValueError("Temperature must be between -100 and +100")


def validate_humidity(rel_humidity):
    """
    Validates relative humidity:
    - relative humidity must be below 100%
    - relative humidity must be above 0%

    Input:
    - humidity (in %)
    """
    if not isinstance(rel_humidity, (float, int)):
        raise TypeError("Relative Humidity must be int or float")
    if rel_humidity < 0 or rel_humidity > 100:
        raise ValueError("Rel. humidity must be between 0 and 100")


def pressure_function(pressure):
    """
    Calculates the pressure function for the saturation vapor

    Inputs:
       - pressure (in hPa)
    Output:
       - pressure function value
    """
    validate_pressure(pressure)
    return 1.0016 + 3.16 * 1e-6 * pressure - 0.074 / pressure


def calculate_abs_humidity(pressure, temperature, rel_humidity):
    """
    Calculates the absolute humidity

    Steps:
    - we first calculate the saturation vapor pressure in pure phase (e_w)
    - we use the pressure function f(p) to calculate the saturation vapor
        pressure of moist air (e_w_moist)
    - We can then use the ideal gas law, PV = m R T,
            PV = (m/M) R T
        where R is the universal gas constant (8.314 kg m^2 / s^2 mol K),
        and transform it to
            eV = m R_v T
        where R_v is the specific gas constant for water vapor (461.5 J / kg K)
        and then
        m / V = e / (R_v T)
        which is the absolute humidity (i.e. mass of water vapor in a unit

    Inputs:
        - pressure (in hPa)
        - temperature (in C)
        - relative humidity (in %)
    Output:
        - humidity measurement value

        """
    validate_pressure(pressure)
    validate_temperature(temperature)
    validate_humidity(rel_humidity)

    # saturation vapor pressure in pure phase
    e_w = 6.112 * math.exp(17.62 * temperature / (243.12 + temperature))

    # saturation vapor pressure in moist air
    e_w_moist = pressure_function(pressure=pressure) * e_w

    # actual vapor pressure
    vapor_pressure = e_w_moist * rel_humidity

    # absolute humidity
    return vapor_pressure / (461.5 * (273.15 + temperature))


def convert_pressure(pressure, unit='hPa'):
    """
    Converts pressure from hPa (input) to the desired unit.
    Available options are:
     - hPa (`unit='hPa'`)
     - Pa (`unit='Pa'`)
     - kPa (`unit='kPa'`)
     - atm (`unit='atm'`)
     - mm Hg (`unit='mmHg'`)

    Inputs:
        - pressure (in hPa)
        - unit to convert pressure to (hPa/Pa/kPa/atm/mmHg)
    Output:
        - pressure in desired unit
    """
    validate_pressure(pressure)

    conversion_factor = {"hPa": 1,
                         "Pa": 100,
                         "kPa": 0.1,
                         "atm": 9.8692316931427E-4,
                         "mmHg": 0.750062}

    if unit in conversion_factor:
        return conversion_factor[unit] * pressure

    raise Exception("Unknown pressure unit: " + unit)


def convert_temperature(temperature, unit='C'):
    """
    Converts temperature from Celsius (input) to the desired unit.
    Available options are:
    - Celsius (`unit='C'`)
    - Fahrenheit (`unit='F'`)
    - Kelvin (`unit='K'`)

    Inputs:
        - temperature (in C)
        - unit to convert temperature to (C/F/K)
    Output:
        - temperature in desired unit
    """
    validate_temperature(temperature)

    if unit == 'C':
        return temperature

    if unit == 'F':
        return temperature * (9. / 5) + 32.

    if unit == 'K':
        return temperature + 273.15

    raise Exception("Unknown temperature unit: " + unit)


def round_to_n_significant_digits(value, n_digits):
    """
    Round to n significant digits, e.g. for 1234 the result
    with 2 significant digits would be 1200.
    Input:
        - the value to be rounded
        - the desired number of significant digits
    Output:
        - the value rounded to the desired number of significant digits
    """
    if not isinstance(value, (float, int)):
        raise TypeError("Value must be int or float")
    if not isinstance(n_digits, int):
        raise TypeError("Number of digits must be int")
    if not n_digits > 0:
        raise ValueError("Number of digits must be greater than zero")

    return round(value, n_digits - 1 - int(math.floor(math.log10(abs(value)))))
