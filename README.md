# usps2mqtt

usps2mqtt is a simple way to integrate USPS Informaed Delivery with Home Assistant. 

This is a repackaged version of [USPS Mail Integration with Home Assistant](https://blog.kalavala.net/usps/homeassistant/mqtt/2018/01/12/usps.html) that can be deployed on any host with python 3 and access to your Home Assistant MQTT server. 

The script logs into your email, finds the email from USPS Informed Delivery, gets the count of mail and packages along with photos and then published the results to your MQTT Server.  

## Requirements

This script was written in python3 and requires the installation of some python libraires, and imagemagik 

## Installation
* Clone this repo: `git clone https://github.com/thejeffreystone/usps2mqtt.git`
* cd to dir `usps2mqtt`
* install required python libraries: `pip install -r requirements.txt`
* install imagemagick `sudo apt-get install imagemagick`
* cp env-sample to .env: `cp env-sample .env`
* Edit .env to match your environmnt:

```
# MQTT Hosts details
MQTT_SERVER = 127.0.0.1 
MQTT_SERVER_PORT = 1883

# MQTT User name and Password
MQTT_USERNAME = mqtt
MQTT_PASSWORD = pass

# MQTT Topic
MQTT_USPS_MAIL_TOPIC = house/usps/mails
MQTT_USPS_PACKAGE_TOPIC = house/usps/packages

# Email Host Details
# For Email Hosts:

# GMail	- imap.gmail.com / 993
# Yahoo	- imap.mail.yahoo.com / 993
# Outlook	- imap-mail.outlook.com / 993
 
# Update host and port based on your provider
HOST = imap.gmail.com
PORT = 993

# Your email login creds
USERNAME = email@gmail.com
PASSWORD = pass

# Image Output location
IMAGE_OUTPUT_PATH = /var/www/html/images/

# Update Interval - default 5 mins
SLEEP_TIME_IN_SECONDS = 300

```
 
## Running usps2mqtt

Simple execute `usps2matt.py` 

You will want to automate the execution via cron, pm2, supervisor, or the like. 

## Integrating into Home Assistant

Next you just have to setup some sensors. 

For an example see my [usps package](https://github.com/thejeffreystone/home-assistant-configuration/blob/master/config/packages/usps.yaml).  
 

