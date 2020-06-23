#!/usr/bin/env python3
""" bme280pi: the BME280 Sensor Reader for Raspberry Pi
This package provides:
- an intuitive way to access the Bosch BME280 sensor
- the ability to convert measurements into different units
"""
DOCLINES = (__doc__ or '').split("\n")

import sys

from setuptools import setup, find_packages


if sys.version_info.major < 3 or sys.version_info.minor < 5:
    print("Package is for python 3.5 or later, please upgrade")
    sys.exit(1)


setup(name='bme280pi',
      version='1.0',
      license='MIT',
      description = DOCLINES[0],
      long_description = "\n".join(DOCLINES[2:]),
      author='Marco-Andrea Buchmann',
      url='https://www.github.com/MarcoAndreaBuchmann/bme280pi',
      download_url = 'https://github.com/MarcoAndreaBuchmann/bme280pi/archive/v1.0.tar.gz',
      project_urls={"Bug Tracker": "https://github.com/MarcoAndreaBuchmann/bme280pi/issues",
                    "Source Code": "https://github.com/MarcoAndreaBuchmann/bme280pi"},
      keywords=['Raspberry', 'Pi', 'Raspberry Pi', 'BME280', 'sensor',
                'readout', 'temperature', 'pressure', 'humidity'],
      platforms = ["Linux"],
      python_requires=">=3.5",
      packages=find_packages(),
      tests_require=["pytest"],
      install_requires=['smbus'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Build Tools',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7']
      )
