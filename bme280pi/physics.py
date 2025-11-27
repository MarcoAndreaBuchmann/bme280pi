"""Physics functions for pressure/temperature/humidity/...

Provides functions related to converting humidity from relative
to absolute humidity. Also provides functions for converting
pressure & temperature into different units (e.g. Kelvin, mm Hg),
and to round numbers to a n significant digits.

The following functions are present in this module:
- validate_pressure(pressure)
- validate_temperature(temperature)
- validate_humidity(rel_humidity)
- validate_height_above_sea_level(height_above_sea_level)
- pressure_function(pressure)
- calculate_abs_humidity(pressure, temperature, rel_humidity)
- convert_pressure(pressure, unit='hPa')
- convert_temperature(temperature, unit='C')
- pressure_at_sea_level(pressure, temperature, height_above_sea_level)
- round_to_n_significant_digits(value, n_digits)

source for formulae:
https://planetcalc.com/2167/
https://keisan.casio.com/keisan/image/Convertpressure.pdf
"""

import math
from typing import Union


def validate_pressure(pressure: Union[float, int]) -> None:
    """Validate input pressure.

    Checks that pressure satisfies the following constraints:
    - needs to be positive
    - needs to be smaller than 1100 (largest value ever was 1083)

    A `ValueError` is raised if any of the assumptions are violated.

    Args:
        pressure (float/int): pressure in hPa

    Returns:
        None
    """
    if not isinstance(pressure, (float, int)):
        raise TypeError("Pressure must be int or float")

    if pressure <= 0 or pressure > 1100:
        raise ValueError("Pressure must be between 0 and 1100")


def validate_temperature(temperature: Union[float, int]) -> None:
    """Validate input temperature.

    Checks that temperature satisfies the following constraints:

    - needs to be smaller than 100 degrees (humidity calculations
      don't make much sense above this temperature)
    - needs to be larger than -100 (same reason)

    A `ValueError` is raised if any of the assumptions are violated.

    Args:
        temperature (float/int): temperature in degrees Celsius

    Returns:
        None
    """
    if not isinstance(temperature, (float, int)):
        raise TypeError("Temperature must be int or float")

    if temperature < -100 or temperature > 100:
        raise ValueError("Temperature must be between -100 and +100")


def validate_humidity(rel_humidity: Union[float, int]) -> None:
    """Validate input humidity.

    Checks that humidity satisfies the following constraints:
    - relative humidity must be below 100%
    - relative humidity must be above 0%

    A `ValueError` is raised if any of the assumptions are violated.

    Args:
        rel_humidity (float/int): relative humidity in percent (i.e. 0-100)

    Returns:
        None
    """
    if not isinstance(rel_humidity, (float, int)):
        raise TypeError("Relative Humidity must be int or float")
    if rel_humidity < 0 or rel_humidity > 100:
        raise ValueError("Rel. humidity must be between 0 and 100")


def validate_height_above_sea_level(height_above_sea_level: Union[float, int]) -> None:
    """Validate height above sea level.

    Checks that height above sea level satisfies the following constraints:
    - needs to be positive
    - needs to be smaller than 11000 (limit of validity of conversion formula)

    A `ValueError` is raised if any of the assumptions are violated.

    Args:
        height_above_sea_level (float/int): height above sea level in meters

    Returns:
        None
    """
    if not isinstance(height_above_sea_level, (float, int)):
        raise TypeError("Height above sea level must be int or float")

    if height_above_sea_level <= 0 or height_above_sea_level > 11000:
        raise ValueError("Height above sea level must be between zero " + "and 11000")


def pressure_function(pressure: Union[float, int]) -> float:
    """Saturation vapor pressure function.

    Calculates the relevant factor to convert the saturation vapor pressure
    in pure phase to the saturation vapor pressure in moist air.

    Args:
        pressure (int/float): pressure in hPa

    Returns:
        float: factor to convert saturation vapor pressure
    """
    validate_pressure(pressure)
    return 1.0016 + 3.16 * 1e-6 * pressure - 0.074 / pressure


def calculate_abs_humidity(
    pressure: Union[float, int],
    temperature: Union[float, int],
    rel_humidity: Union[float, int],
) -> float:
    """Calculate the absolute humidity.

    The absolute humidity is calculated in the following steps:

    1. Saturation vapor pressure over water (Magnus formula):
       .. math:: e_w(T) = 6.112 \cdot \exp\left( \frac{17.62 \cdot T}{T + 243.12} \right)

    2. Enhancement factor :math:`f(p)` accounts for real moist air

    3. Actual vapor pressure:
       .. math:: e = \frac{\text{rel\_humidity}}{100} \cdot f(p) \cdot e_w(T)

    4. Absolute humidity (ideal gas law for water vapor):
       .. math:: AH = \frac{e \cdot 100}{R_v \cdot T_K} \cdot 2.16679
       .. math:: \quad\text{with } R_v = 461.5\,\text{J}\,\text{kg}^{-1}\,\text{K}^{-1}

       The constant 2.16679 converts from hPa·K to g/m³.

    Args:
        pressure (int/float): pressure in hPa
        temperature (int/float): temperature in degrees Celsius
        rel_humidity (int/float): relative humidity in percent (0-100)

    Returns:
        float: humidity measurement value
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


def convert_pressure(pressure: Union[float, int], unit: str = "hPa") -> float:
    """Pressure in user-specified unit.

    Converts pressure from hPa (input) to the desired unit.

    Available options are:

     - hPa (`unit='hPa'`)
     - Pa (`unit='Pa'`)
     - kPa (`unit='kPa'`)
     - atm (`unit='atm'`)
     - mm Hg (`unit='mmHg'`)

    Args:
        pressure (int/float): pressure in hPa
        unit (str): unit TO CONVERT PRESSURE TO (hPa/Pa/kPa/atm/mmHg)

    Returns:
        float: pressure in specified unit
    """
    validate_pressure(pressure)

    conversion_factor = {
        "hPa": 1,
        "Pa": 100,
        "kPa": 0.1,
        "atm": 9.8692316931427e-4,
        "mmHg": 0.750062,
    }

    if unit in conversion_factor:
        return conversion_factor[unit] * pressure

    raise Exception("Unknown pressure unit: " + unit)


def convert_temperature(
    temperature: Union[float, int], unit: str = "C"
) -> Union[float, int]:
    """Temperature in user-specified unit.

    Converts temperature from Celsius (input) to the desired unit.
    Available options are:
    - Celsius (`unit='C'`)
    - Fahrenheit (`unit='F'`)
    - Kelvin (`unit='K'`)

    Args:
        temperature (int/float): temperature in degrees Celsius
        unit (str): unit to convert the temperature to (C/F/K)

    Returns:
        float: temperature in desired unit
    """
    validate_temperature(temperature)

    if unit == "C":
        return temperature

    if unit == "F":
        return temperature * (9.0 / 5) + 32.0

    if unit == "K":
        return temperature + 273.15

    raise Exception("Unknown temperature unit: " + unit)


def pressure_at_sea_level(
    pressure: Union[float, int],
    temperature: Union[float, int],
    height_above_sea_level: Union[float, int],
) -> float:
    r"""Convert pressure to pressure at sea level.

    Uses a simple formula to convert the observed pressure to the equivalent
    pressure at sea level. The pressure at sea level is a commonly quoted
    quantity, often referred to as QFF whereas the "local" observed pressure
    is referred to as QFE.

    .. math::

        e = -\frac{g}{R_d \gamma}
        f = \left(1 + \frac{\gamma \cdot h}{T - \gamma\cdot h}\right)
        p = p_0 * f ^ e

    where `e` is the exponent, `f` is the correction factor, `gamma` is the
    derivative `dT/dz` (which is approx. -0.0065 K/m), g is the gravitational
    acceleration in free fall (9.80665 m/s^2), `T` is the temperature,
    `R_d` is the specific gas constant of dry air (287 J/kg/K), `p` is the
    observed pressure, and `p_0` is the pressure at sea level. All calculations
    are in SI units.

    Args:
        pressure (float/int): pressure in hPa
        temperature (float/int): temperature in degrees Celsius
        height_above_sea_level (float/int): height above sea level in meters

    Returns:
        float: equivalent pressure at sea level in hPa
    """
    validate_pressure(pressure)
    validate_temperature(temperature)
    validate_height_above_sea_level(height_above_sea_level)

    gamma = -0.0065
    gravitational_acc = 9.80665
    r_d = 287
    temp = convert_temperature(temperature, unit="K")

    exponent = -gravitational_acc / (r_d * gamma)
    nominator = gamma * height_above_sea_level
    denominator = temp - gamma * height_above_sea_level
    base = 1 + nominator / denominator

    return float(pressure / pow(base, exponent))


def round_to_n_significant_digits(value: Union[float, int], n_digits: int) -> float:
    """Round to n significant digits.

    Rounds a number to n significant digits, e.g. for 1234 the result
    with 2 significant digits would be 1200.

    Args:
        value (float/int): the value to be rounded
        n_digits (int): the desired number of significant digits

    Returns:
        float: the value rounded to the desired number of significant digits
    """
    if not isinstance(value, (float, int)):
        raise TypeError("Value must be int or float")
    if not isinstance(n_digits, int):
        raise TypeError("Number of digits must be int")
    if not n_digits > 0:
        raise ValueError("Number of digits must be greater than zero")

    return round(value, n_digits - 1 - int(math.floor(math.log10(abs(value)))))
