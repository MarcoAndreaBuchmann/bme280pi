"""
This is the bme280pi package, to read out the BME280 sensor on Raspberry Pi.

Here's a quick overview of how this package can be used:

1) Import the Sensor class:
`from bme280pi import Sensor`
2) Initialize a `Sensor` object:
`sensor = Sensor()`
3) Get the sensor data:
`data = sensor.get_data()`

You can also just fetch the temperature, the pressure, or the humidity with
the individual `.get_temperature()`, `.get_pressure`, and `get_humidity`
functions.

The standard units are degrees Celsius (C) for temperature, hectoPascal (hPa)
for pressure, and percentage for humidity. Other units are supported for
temperature (F and K) and pressure (mm Hg, atm, Pa, kPa), and the humidity
can also be indicated in absolute terms (i.e. g per m^3).

For more in-depth information see the individual docstrings of the functions
of the `Sensor` class.
"""

from .sensor import Sensor

__all__ = ["Sensor"]
