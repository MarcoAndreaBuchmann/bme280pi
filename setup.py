"""
Setup script for bme280pi
"""

import sys

from setuptools import setup, find_packages


if sys.version_info.major < 3 or sys.version_info.minor < 5:
    print("Package is for python 3.5 or later, please upgrade")
    sys.exit(1)


setup(name='bme280pi',
      version='1.0',
      license='MIT',
      description='Package to read out BME280 sensor on Raspberry Pi',
      author='Marco-Andrea Buchmann',
      url='https://www.github.com/MarcoAndreaBuchmann/bme280pi',
      download_url = 'https://github.com/MarcoAndreaBuchmann/bme280pi/archive/v1.0.tar.gz',
      keywords=['Raspberry', 'Pi', 'Raspberry Pi', 'BME280', 'sensor',
                'readout', 'temperature', 'pressure', 'humidity'],
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
