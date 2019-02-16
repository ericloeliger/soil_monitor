# soil_monitor
Script to monitor soil wetness and air temperature & humidity

## Overview
This script is for monitoring the soil wetness of one or more plants, as well as the air temperature & humidity. 

## Hardware Requirements
### Mandatory
- Raspberry Pi
    - I run Raspbian on a Model B3
- Soil Wetness Sensor
    - Commonly referred to as YL-69 sensors
    - I used these https://www.amazon.com/dp/B071F4RDHY/ref=cm_sw_em_r_mt_dp_U_wsdACbNXHW42N
- MCP3008
    -  Used as DAQ to read analog sensor voltage
    - I got mine here https://www.adafruit.com/product/856

### Optional
- Wi-Fi Temperature & Humidity Sensor
    - Provides additional environment context
    - My personal favorite http://projects.privateeyepi.com/WIFI-Sensor
- Enclosure for YL-69 circuit board
    - 'add thingiverse link'


## Software Requirements
- Python 3
- Non-standard Python modules
    - pip install adafruit-io
    - pip install Adafruit-GPIO
    - pip install adafruit-circuitpython-mcp3xxx
- Custom modules
    - https://github.com/ericloeliger/python-common-modules
    - send_to_adafruit_io_feed
        - Common module for sending data to AdafruitIO feeds using MQTT
    - privateEyePiSensor
        - Common module for reading data from the PrivateEyePi wifi temp & humidity sensor