# bme280pi: the BME280 Sensor Reader for Raspberry Pi


## How to Install

### Enable the I2C Interface

1) `sudo raspi-config`
2) Select "Interfacing Options"
3) Highlight the "I2C" option, and activate "Select" (use tab)
4) Answer the question if you'd like the ARM I2C interface to be enabled with "Yes"
5) Select "Ok"
6) Reboot

For a walk-through with screenshots see reference [2] below.

### Install Utilities

Install `python-smbus` and `i2ctools`:
`sudo apt-get update && sudo apt-get install -y python-smbus i2c-tools`

Then, shut down your Raspberry Pi:
`sudo halt`
 
### Connect the BME280 sensor

![ModuleSetup](http://gilles.thebault.free.fr/IMG/jpg/raspi_bme280_bb.jpg)

### Install This Module

You can then install this module by running `python setup.py install`

### Using it in your script

You can initialize the sensor class as follows:
```
from bme280pi import Sensor

sensor = Sensor()
```

You can then use the `sensor` to fetch data, `sensor.get_data()`, which will return a dictionary
with temperature, humidity, and pressure readings.

You can also just get the temperature (`sensor.get_temperature()`),
just the pressure (`sensor.get_pressure()`), or
just the humidity (`sensor.get_humidity()`).

Note that all commands support user-specified units, e.g. `sensor.get_temperature(unit='F')`,
or `sensor.get_pressure(unit='mmHg')`.

You can e.g. query the sensor every 10 seconds, and add the results to a dictionary, and then
turn that into a pandas DataFrame and plot that (requires matplotlib and pandas):

```
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



### References

[1] https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/

[2] https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/


