#!/usr/bin/python3
# eric.loeliger@gmail.com

# Change Log 
# 2/2/19 - started
#   V3 is just production-ized V2
# 2/7/19 - added sending to AdafruitIO
# 2/16/19 - add upper threshold to detect if sensor is out of soil

# import modules
import configparser
import logging
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import time
import smtplib
from email.mime.text import MIMEText
import datetime


this_script_name = 'soil_monitor'

#get pi nickname
nickname_file = open('//etc/nickname','r').read().split('\n')
piName = nickname_file[0]

# load properties from file
config = configparser.ConfigParser()
config.read('//home/pi/Python_Scripts/%s/%s_properties.ini' % (this_script_name,this_script_name))

# DEBUG switch  0 = Production, 1 = debug
debugMode = int(config['general']['DebugMode'])

# Logger configuration
log_name = config['logger.config']['LogName']
log_path_linux = config['logger.config']['LogPathLinux']

logger = logging.getLogger('%s.py' % this_script_name)
handler = logging.FileHandler('%s%s' % (log_path_linux,  log_name))
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# import custom modules
import send_to_adafruit_io_feed
import privateEyePiSensor

## This is a generic function to send emails
def sendEmail(msg):
    logger.info('Entered sendEmail function')
    msg['From'] = gmail_user
    msg['To'] = ", ".join(recipients)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(gmail_user, gmail_password)
    smtpserver.sendmail(gmail_user, recipients, msg.as_string())
    logger.info("Mail Sent to %s" % recipients)
    smtpserver.quit()
    logger.info("SMTP server closed")
    logger.info('sendEmail function complete')


try:
    logger.info("########## Begin %s.py ##########" % this_script_name)

    # import email properties
    gmail_user = config['email']['outbound_user']
    gmail_password = config['email']['outbound_password']
    smtpserver = smtplib.SMTP(config['email']['outbound_smtp_server'])
    recipients = [config['email']['recipients']]


    # import sensor properties
    sensor_dict = {}
    sensor_qty = int(config['sensor.1']['SensorQuantity'])
    current_sensor = 1
    while current_sensor <= sensor_qty:
        sensor_config_id = 'sensor.%s' % current_sensor
        sensor_name = config[sensor_config_id]['SensorID']
        sensor_dict[sensor_name] = {}
        sensor_dict[sensor_name]['config_id'] = sensor_config_id
        sensor_dict[sensor_name]['url'] = config[sensor_config_id]['SensorURL']
        sensor_dict[sensor_name]['version'] = int(config[sensor_config_id]['SensorVersion'])
        current_sensor = current_sensor + 1
    logger.debug("Sensor dict: %s" % sensor_dict)

    # setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    pin = 17
    GPIO.setup(pin, GPIO.OUT)

    # Hardware SPI configuration:
    SPI_PORT   = 0
    SPI_DEVICE = 0
    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

    # turn sensor on, wait to stabilize
    GPIO.output(pin,1)
    logger.debug("Sensor on")
    sensor_stabilization_time = int(config['soil']['sensor_stabilization_time'])
    logger.debug("Waiting %s seconds for sensor to stabilize" % sensor_stabilization_time)
    time.sleep(sensor_stabilization_time)

    # read sensor value
    raw_sensor_value = mcp.read_adc(0)
    logger.debug('Raw sensor value: %s' % raw_sensor_value)

    # turn sensor off
    GPIO.output(pin,0)
    logger.debug("Sensor off")

    # send value to AdafruitIO
    # define feed dictionary
    feedDictionary = {}
    feedDictionary['wetnessProbe01'] = {}
    feedDictionary['wetnessProbe01']['feedID'] = config['adafruit.io']['WetnessFeedID01']
    feedDictionary['wetnessProbe01']['value'] = raw_sensor_value
    logger.debug("Adafruit feed dictionary: %s" % feedDictionary)
    send_to_adafruit_io_feed.sendToAdafruitIOFeed(config['adafruit.io']['ClientUser'],config['adafruit.io']['ClientKey'],feedDictionary)

    # see if plant needs to be watered
    threshold = int(config['soil']['threshold'])
    out_of_soil_threshold = int(config['soil']['OutOfSoilThreshold'])

    if raw_sensor_value < threshold:
        logger.info('Soil is dry - watering needed!')

        ## Compose email message and send
        msg = MIMEText('Soil is dry and needs to be watered.  Sensor value: %s' % raw_sensor_value)
        msg['Subject'] = 'Soil Monitoring Alert from %s' % piName
        sendEmail(msg)

    elif raw_sensor_value > out_of_soil_threshold:
        logger.info("Sensor likely out of soil!")

        ## Compose email message and send
        msg = MIMEText('Sensor likely out of soil, please check.  Sensor value: %s' % raw_sensor_value)
        msg['Subject'] = 'Soil Monitoring Alert from %s' % piName
        sendEmail(msg)
    
    else:
        logger.info('Soil is wet - no watering needed')


    # get temperature & humidity readings
    temp_humid_response = privateEyePiSensor.getWifiTempHumidityReadings(sensor_dict)
    logger.debug("Temp & humidity readings: %s" % temp_humid_response)

    # send value to AdafruitIO
    # define feed dictionary
    feedDictionary = {}
    for sensor in temp_humid_response:
        temp_key = '%s_temperature' % sensor
        humidity_key = '%s_humidity' % sensor
        feedDictionary[temp_key] = {}
        feedDictionary[humidity_key] = {}
        feedDictionary[temp_key]['feedID'] = config['adafruit.io']['TemperatureFeedID01']
        feedDictionary[temp_key]['value'] = temp_humid_response[sensor]['temperature']
        feedDictionary[humidity_key]['feedID'] = config['adafruit.io']['HumidityFeedID01']
        feedDictionary[humidity_key]['value'] = temp_humid_response[sensor]['humidity']
    logger.debug("Adafruit feed dictionary: %s" % feedDictionary)
    send_to_adafruit_io_feed.sendToAdafruitIOFeed(config['adafruit.io']['ClientUser'],config['adafruit.io']['ClientKey'],feedDictionary)

except Exception as e:
    logger.exception("Exception occured: %s" % e)
    msg = MIMEText("%s soil monitoring script has encountered an exception at %s UTC. \n \n Exception: %s" % (piName,datetime.datetime.utcnow(),e))
    msg['Subject'] = 'Soil Monitoring EXCEPTION REPORT from %s' % piName
    sendEmail(msg)

finally:
    # clean up
    GPIO.cleanup()
    logger.info("########## End %s.py ##########" % this_script_name)