#!/usr/bin/env python3

"""
Make sure you change the parameters - username, password, mailbox,
paths and options.
"""

import email
import datetime, imaplib, re, sys
import os
import time
import subprocess
import paho.mqtt.client as mosquitto
from shutil import copyfile

from dotenv import load_dotenv
load_dotenv()

# MQTT Server Address and Port
MQTT_SERVER = os.getenv("MQTT_SERVER")
MQTT_SERVER_PORT = int(os.getenv("MQTT_SERVER_PORT"))

# MQTT User name and Password
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

MQTT_USPS_MAIL_TOPIC = os.getenv("MQTT_USPS_MAIL_TOPIC")
MQTT_USPS_PACKAGE_TOPIC = os.getenv("MQTT_USPS_PACKAGE_TOPIC")

SLEEP_TIME_IN_SECONDS = int(os.getenv("SLEEP_TIME_IN_SECONDS"))

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
folder   = 'inbox'

GIF_FILE_NAME = "todays_mails.gif"
GIF_MAKER_OPTIONS = '/usr/bin/convert  -delay 300 -loop 0 '
IMAGE_OUTPUT_PATH = os.getenv("IMAGE_OUTPUT_PATH")

# Login Method
###############################################################################
def login():
    account = imaplib.IMAP4_SSL(HOST, PORT)

    try:
        rv, data = account.login(USERNAME, PASSWORD)
        print_message ("Logged into your email server successfully!")
    except imaplib.IMAP4.error:
        print_message ('Failed to authenticate using the given credentials. Check your username, password, host and port.')
        sys.exit(1)

    return account

# Select folder inside the mailbox
###############################################################################
def selectFolder(account, folder):
    rv, mailboxes = account.list()
    rv, data = account.select(folder)
    print_message ("Selecting folder '{}'".format(folder))

# Creates GIF image based on the attachments in the inbox
###############################################################################
def get_mails(account):
    today = get_formatted_date()
    image_count = 0

    rv, data = account.search ( None, 
                              '(FROM "USPS" SUBJECT "Informed Delivery Daily Digest" SINCE "' + 
                              today + '")')
    if rv == 'OK':
        for num in data[0].split():
            rv, data = account.fetch(num, '(RFC822)')
            msg = email.message_from_string(data[0][1].decode('utf-8'))
            images = []
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                if '_' in part.get_filename():
                    print_message('Found an advertisement, skipping it!')
                    continue

                filepath = IMAGE_OUTPUT_PATH + part.get_filename()
                fp = open( filepath, 'wb' )
                fp.write(part.get_payload(decode=True))
                images.append(filepath)
                image_count = image_count + 1
                fp.close()
            
            print_message ('Found {} mails and images in your email.'.format(image_count))

            if image_count > 0:
                all_images = ""

                for image in images:
                    all_images = all_images + image + " "

                print_message ("Creating animated GIF out of {} images.".format(image_count))
                os.system( GIF_MAKER_OPTIONS + all_images + 
                           IMAGE_OUTPUT_PATH + GIF_FILE_NAME )

                print_message ("Cleaning up...")
                for image in images:
                    os.remove(image)
    
    if (image_count == 0):
        print_message("Found '{}' mails".format(image_count))

    return image_count

# Returns today in specific format

# Returns today in specific format
###############################################################################
def get_formatted_date():
    return datetime.datetime.today().strftime('%d-%b-%Y')

# gets packages count
###############################################################################
def package_count(account):
    count = 0 
    today = get_formatted_date()

    rv, data = account.search(None, 
              '(FROM "auto-reply@usps.com" SUBJECT "Item Delivered" SINCE "' + 
              today + '")')

    if rv == 'OK':
        count = len(data[0].split())

    print_message("Found '{}' packages".format(count))
    #os.system("mosquitto_pub -h 192.168.7.67 -p 1883 -t 'house/usps/packages' -m '%d' -r -u hass -P wearethestonesjks" % count)
    return count

# Prints message to console
###############################################################################
def print_message(message):
    print("{} USPS: {}".format(datetime.datetime.today().strftime('%d-%b-%Y %H:%m:%S%p'), message))

# OnConnect Callback
###############################################################################
def on_connect(mosq, userdata, flags, rc):
    print_message("Connected with return code: {}".format(str(rc)))

# OnLog Callback
###############################################################################
def on_log(mosq, obj, level, string):
    print_message(string)

# Primary logic for the component starts here
###############################################################################

# Primary logic for the component starts here
###############################################################################
try:
    while True:
        try:
            # create a new MQTT Client Object
            mqttc = mosquitto.Mosquitto()
            # Set event callbacks
            mqttc.on_connect = on_connect
            # Uncomment below line to enable debug/console messages
            # mqttc.on_log = on_log
            # Connect to MQTT using the username/password set above
            mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            mqttc.connect(MQTT_SERVER, MQTT_SERVER_PORT)

            print_message ("Connected to MQTT Server successfully")
        except Exception as ex:
            print_message ("Error connecting to MQTT.")
            print_message (str(ex))
            sys.exit(1)

        try:
            account = login()
            selectFolder(account, folder)
        except Exception as exx:
            print_message ("Error connecting logging into email server.")
            print_message (str(exx))
            sys.exit(1)
        # Get the mail count and drop it in the MQTT
        mc = get_mails(account)
        mqttc.publish(MQTT_USPS_MAIL_TOPIC, str(mc), qos=0, retain=False)

        # Get the package count and drop it in the MQTT
        pc = package_count(account)
        mqttc.publish(MQTT_USPS_PACKAGE_TOPIC, str(pc), qos=0, retain=False)

        # if there are no mails, make sure you delete the old file, 
        # so that the next day, you don't see yesterday's mails
        # when there are no mails, copy nomail.jpg as your default file
        if mc == 0:
            os.remove(IMAGE_OUTPUT_PATH + GIF_FILE_NAME)
            copyfile("nomail.gif", IMAGE_OUTPUT_PATH + GIF_FILE_NAME)

        # disconnect from MQTT
        mqttc.disconnect()
        print_message ("Disconnected MQTT successfully. Will check your mails again in {} seconds.".format(str(SLEEP_TIME_IN_SECONDS)))

        # sleep for 5 minutes before trying it again
        #time.sleep(SLEEP_TIME_IN_SECONDS)
        sys.exit(1)
except Exception as e:
    print_message ("Error occured while either processing email or publishing messages to MQTT.")
    print_message (str(e))
    sys.exit(1)
