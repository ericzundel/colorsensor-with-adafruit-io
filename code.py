# SPDX-FileCopyrightText: 2022 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import board
import busio
import ipaddress
import os
import socketpool
import time
import wifi

import adafruit_tcs34725

import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there and don't commit them to git!")
    raise


# Create sensor object, communicating over the board's default I2C bus
i2c = busio.I2C(board.GP1, board.GP0)  # uses board's native I2C port
sensor = adafruit_tcs34725.TCS34725(i2c)


# Change sensor integration time to values between 2.4 and 614.4 milliseconds
sensor.integration_time = 150

# Change sensor gain to 1, 4, 16, or 60
sensor.gain = 4

print()
print("Connecting to WiFi")

#  connect to your SSID
wifi.radio.connect(secrets['wifi_ssid'], secrets['wifi_password'])

print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)

#  prints MAC address to REPL
print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

#  prints IP address to REPL
print("My IP address is", wifi.radio.ipv4_address)

#  pings Google
ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))


# Setup a feed named `testfeed` for publishing.
#default_topic = secrets['aio_username'] + "/feeds/colorsensor-training-data"
default_topic = 'colorsensor-training-data'

### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print(f"Connected to MQTT broker! Listening for topic changes on {default_topic}")
    # Subscribe to all changes on the default_topic feed.
    client.subscribe(default_topic)


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from MQTT Broker!")


def message(client, topic, message):
    """Method callled when a client's subscribed feed has a new
    value.
    :param str topic: The topic of the feed with a new value.
    :param str message: The new value
    """
    print(f"New message on topic {topic}: {message}")

def read_color_input():
    """Ask the human to select the color"""
    while True:
        print("What color?  (R)ed (P)urple (O)range (Y)ellow (G)reen [R/P/O/Y/G]: ")
        response = input().upper()
        if response is 'R':
            return 'red'
        elif response is 'P':
            return 'purple'
        elif response is 'O':
            return 'orange'
        elif response is 'Y':
            return 'yellow'
        elif response is 'G':
            return 'green'

# Get a socket from the socket pool
socket_pool = socketpool.SocketPool(wifi.radio)

print("Setting up MQTT client")

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=1883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=socket_pool,
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

print("Connecting to MQTT server")
# Connect the client to the MQTT broker.
io.connect()

while True:
    # Poll for incoming messages
    try:
        io.loop()
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        wifi.connect()
        io.reconnect()
        continue

    train_color = read_color_input()

    print(
        "RGB color as 8 bits per channel int: #{0:02X} or as 3-tuple: {1}".format(
             sensor.color, sensor.color_rgb_bytes
        )
    )

    # Send a new message
    print("Sending value to feed '%s'" % (default_topic))

    # This is dummy data, but in the format I anticipate we will use for the training machine.
    io.publish(default_topic, "{'temperature': %d, 'r' : %d, 'g': %d, 'b': %d, 'lux' : %d, 'color': '%s'}" %
        (
            sensor.color_temperature,
            sensor.color_rgb_bytes[0],
            sensor.color_rgb_bytes[1],
            sensor.color_rgb_bytes[2],
            sensor.lux,
            train_color
        )
    )

    # To do this in a loop, we have to make sure not to exceed the adafruit io limits. For the free plan that's
    # 30 samples per minute.
    #time.sleep(2)]
    break

print("View data at https://io.adafruit.com/%s/feeds/colorsensor-training-data" % (secrets["aio_username"]))
