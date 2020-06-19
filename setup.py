from setuptools import setup, find_packages

import sys


if sys.version_info.major < 3 or sys.version_info.minor < 5:
    print("I'm only for 3.5 or later, please upgrade")
    sys.exit(1)


setup(name='bme280pi',
      version='0.1',
      description='Package to read out BME280 sensor on Raspberry Pi',
      author='Marco-Andrea Buchmann',
      url='https://www.github.com/MarcoAndreaBuchmann/bme280pi',
      packages=find_packages(),
      setup_requires=["pytest-runner"],
      tests_require=["pytest", "mock"],
      install_requires=['smbus'],
      )
