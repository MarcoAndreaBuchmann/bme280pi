"""
Provides functions related to converting humidity from relative
to absolute humidity. Also provides functions for converting
pressure & temperature into different units (e.g. Kelvin, mm Hg),
and to round numbers to a n significant digits.

source for formulae:
https://planetcalc.com/2167/
"""

import math


def pressure_function(pressure):
    """
    Calculates the pressure function for the saturation vapor
    Inputs:
       - pressure (in hPa)
    Output:
       - pressure function value
    """
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

        """
    # saturation vapor pressure in pure phase
    e_w = 6.112 * math.exp(17.62 * temperature / (243.12 + temperature))

    # saturation vapor pressure in moist air
    e_w_moist = pressure_function(pressure=pressure) * e_w

    # actual vapor pressure
    vapor_pressure = e_w_moist * rel_humidity

    # absolute humidity
    return vapor_pressure / (461.5 * (273.15 + temperature))


def convert_pressure(pressure, unit):
    """
    Converts pressure from hPa (input) to the desired unit.
    Available options are:
     - hPa (`unit='hPa'`)
     - Pa (`unit='Pa'`)
     - kPa (`unit='kPa'`)
     - atm (`unit='atm'`)
     - mm Hg (`unit='mmHg'`)
    """
    if unit == "hPa":
        return pressure
    if unit == "Pa":
        return 100 * pressure
    if unit == "kPa":
        return 0.1 * pressure
    if unit == "atm":
        return pressure * 9.8692316931427E-4
    if unit == "mmHg":
        return pressure * 0.750062

    raise Exception("Unknown pressure unit: " + unit)


def convert_temperature(temperature, unit):
    """
    Converts temperature from Celsius (input) to the desired unit.
    Available options are:
    - Celsius (`unit='C'`)
    - Fahrenheit (`unit='F'`)
    - Kelvin (`unit='K'`)
    """
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
    """

    return round(value, n_digits - 1 - int(math.floor(math.log10(abs(value)))))
