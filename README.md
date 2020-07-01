[![Build Status](https://github.com/MarcoAndreaBuchmann/bme280pi/workflows/Tests/badge.svg)](https://github.com/MarcoAndreaBuchmann/bme280pi/actions?query=workflow%3ATests)
[![Test Coverage](https://api.codeclimate.com/v1/badges/74442c7128065652d6da/test_coverage)](https://codeclimate.com/github/MarcoAndreaBuchmann/bme280pi/test_coverage)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/fb51e4dac5ee4e4bbf55c6615aae3597)](https://app.codacy.com/manual/MarcoAndreaBuchmann/bme280pi/dashboard)
[![Maintainability](https://api.codeclimate.com/v1/badges/74442c7128065652d6da/maintainability)](https://codeclimate.com/github/MarcoAndreaBuchmann/bme280pi/maintainability)
[![pypi](https://img.shields.io/pypi/v/bme280pi.svg)](https://pypi.org/project/bme280pi/)

# bme280pi: the BME280 Sensor Reader for Raspberry Pi

## How to Install

### Enable the I2C Interface

1) `sudo raspi-config`
2) Select "Interfacing Options"
3) Highlight the "I2C" option, and activate "Select" (use tab)
4) Answer the question if you'd like the ARM I2C interface to be enabled with "Yes"
5) Select "Ok"
6) Reboot

For a walk-through with screenshots see the references below.

### Install Utilities

Install `python-smbus` and `i2ctools`:
`sudo apt-get update && sudo apt-get install -y python-smbus i2c-tools`

Then, shut down your Raspberry Pi: `sudo halt` . Disconnect your Raspberry Pi power supply.
You are now ready to connect the BME280 sensor.
 
### Connect the BME280 sensor

![ModuleSetup](https://i.imgur.com/8i3sSlC.png)

### Install This Module

### Installing With pip (Recommended)

You can then install this module by running `pip install bme280pi`

### Installing From Source

If you want the latest version, you can check out the sources and install the
package yourself:

```bash
git clone https://github.com/MarcoAndreaBuchmann/bme280pi.git
cd bme280pi
python setup.py install
```

### Using it in your script

You can initialize the sensor class as follows:

```python
from bme280pi import Sensor

sensor = Sensor()
```

You can then use the `sensor` object to fetch data, `sensor.get_data()`, which will return a dictionary
with temperature, humidity, and pressure readings.

You can also just get the temperature (`sensor.get_temperature()`),
just the pressure (`sensor.get_pressure()`), or
just the humidity (`sensor.get_humidity()`).

Note that all commands support user-specified units, e.g. `sensor.get_temperature(unit='F')`,
or `sensor.get_pressure(unit='mmHg')`.

You can e.g. query the sensor every 10 seconds, and add the results to a dictionary, and then
turn that into a pandas DataFrame and plot that (requires matplotlib and pandas):

```python
import time
import datetime

import pandas
import matplotlib.pyplot as plt

from bme280pi import Sensor

measurements = {}

for i in range(20):
    measurements[datetime.datetime.now()] = sensor.get_data()
    time.sleep(10)

measurements = pd.DataFrame(measurements).transpose()

plt.figure()
plt.subplot(2, 2, 1)
measurements['temperature'].plot()
plt.title("Temperature (C)")

plt.subplot(2, 2, 2)
measurements['pressure'].plot()
plt.title("Pressure (hPa)")

plt.subplot(2, 2, 3)
measurements['humidity'].plot()
plt.title("Relative Humidity (%)")

plt.savefig("Measurements.png")
```

### Reporting Issues

Please feel free to report any issues you encounter at the
[issue tracker](https://github.com/MarcoAndreaBuchmann/bme280pi/issues).

### References

[Bosch BME280 Data Sheet](https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/)

[Raspberry-Spy: Using BME280 sensor in python](https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/)
