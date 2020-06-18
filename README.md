# bme280pi: the BME280 sensor reader for Raspberry Pi


## How to install

### Enable the I2C Interface

1) `sudo raspi-config`
2) Select "Interfacing Options"
3) Highlight the "I2C" option, and activate "Select" (use tab)
4) Answer the question if you'd like the ARM I2C interface to be enabled with "Yes"
5) Select "Ok"
6) Reboot

### Install Utilities

Install Â`python-smbus` and `i2ctools`:
`sudo apt-get update && sudo apt-get install -y python-smbus i2c-tools`

Then, shut down your Raspberry Pi:
`sudo halt`
 
### Connect the BME280 sensor

![ModuleSetup](https://www.raspberrypi-spy.co.uk/wp-content/uploads/2016/07/BME280-Module-Setup.png)
### References

https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/
https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/


