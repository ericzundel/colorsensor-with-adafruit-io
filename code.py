# SPDX-FileCopyrightText: 2024 Eric Z. Ayers
#
# SPDX-License-Identifier: Creative Commons Zero 1.0

"""Collect training data from a color sensor and publish it to Adafruit IO """

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

##################
# *EDIT*
# Set configurable values below
# Feed name for Adafruit IO
default_topic = "colorsensor-training-data"

# milliseconds to gather color data
sensor_integration_time = 150

# manually override the color sensor gain
sensor_gain = 4

# Collect this many samples each time we prompt the user
num_samples = 5

# Set the max data values to send per minute 30/min is the free AdafruitIO limit.
# When this rate is exceeded, the code will add a delay to slow down the rate.
max_send_rate = 30

#
# End of editable config values
##################

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi secrets are kept in secrets.py, please add them there and don't commit them to git!"
    )
    raise

# Create sensor object, communicating over the board's default I2C bus
i2c = busio.I2C(board.GP1, board.GP0)  # uses board's native I2C port
sensor = adafruit_tcs34725.TCS34725(i2c)

# Change sensor gain to 1, 4, 16, or 60
sensor.gain = sensor_gain
# Change sensor integration time to values between 2.4 and 614.4 milliseconds
sensor.integration_time = sensor_integration_time

def connect_to_wifi():
    print()
    print("Connecting to WiFi...", end="")

    wifi.radio.connect(secrets["wifi_ssid"], secrets["wifi_password"])

    #  prints IP address to REPL
    print("Connected: IP address %s", wifi.radio.ipv4_address, end="")

    #  pings Google DNS server to test connectivity
    ipv4 = ipaddress.ip_address("8.8.4.4")
    print(
        " Internet up. Ping to google.com in: %f ms"
        % (wifi.radio.ping(ipv4) * 1000)
    )

###########
# Define MQTT callback methods which are called when events occur
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


# end MQTT callbacks
###########


def read_color_input():
    """Ask the human to select the color"""
    while True:
        print()
        print("What color?  (R)ed (P)urple (O)range (Y)ellow (G)reen [R/P/O/Y/G]: ", end="")
        response = input().upper()
        if response is "R":
            return "red"
        elif response is "P":
            return "purple"
        elif response is "O":
            return "orange"
        elif response is "Y":
            return "yellow"
        elif response is "G":
            return "green"


def add_delay(elapsed_time):
    """Try not to exceed the Adafruit IO data rates by pausing between sending batches of data"""
    # For the free plan that's 30 samples per minute.

    # Compute the amount of time we should wait to send based on the max number of samples/minute
    wait_time = (60 / max_send_rate) * num_samples

    # print("Elapsed %d need to wait minimum of %d" % (elapsed_time, wait_time))
    if wait_time > elapsed_time:
        seconds_left = wait_time - elapsed_time
        print(
            "  >>>Throttling data collection. Delaying %d seconds until next sample<<<"
            % (seconds_left)
        )
        time.sleep(seconds_left)
        print()


def read_samples(train_color):
    """Read from the color sensor 'num_samples' times and publish the datapoints"""

    print(
        "Reading %d samples for %s from the sensor and publishing them to AdafruitIO"
        % (num_samples, train_color)
    )

    for i in range(num_samples):
        print(
            "  Sample {0}: Read RGB color: {1} Temperature {2}".format(
                i, sensor.color_rgb_bytes, sensor.color_temperature
            )
        )

        # Send a new message
        print("    Sending value to feed '%s'" % (default_topic))

        # This is dummy data, but in the format I anticipate we will use for the training machine.
        try:
            io.publish(
                default_topic,
                "{'temperature': %d, 'r' : %d, 'g': %d, 'b': %d, 'lux' : %d, 'color': '%s'}"
                % (
                    sensor.color_temperature,
                    sensor.color_rgb_bytes[0],
                    sensor.color_rgb_bytes[1],
                    sensor.color_rgb_bytes[2],
                    sensor.lux,
                    train_color,
                ),
            )
        except (ValueError, RuntimeError, OSError) as e:
            print("Failed to send data, giving up and restarting microcontroller\n", e)
            microcontroller.reset()
            continue


# Initialize WiFI
connect_to_wifi()

# print("Setting up MQTT client for use with Adafruit IO")
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=1883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=socketpool.SocketPool(wifi.radio),
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Initialize an Adafruit IO MQTT Client wrapper
io = IO_MQTT(mqtt_client)

print("Connecting to Adafruit IO MQTT server")
io.connect()

print("Connected!")
print()
print(
    "View data at https://io.adafruit.com/%s/feeds/colorsensor-training-data"
    % (secrets["aio_username"])
)


# Use this value to record the last time data was sent to make sure we don't send too many samples to AdafruitIO
last_data_send_time = 0

while True:

    # Poll for incoming messages. We don't use incoming messages right now, but I think
    # it keeps the library happy
    try:
        io.loop()
    except (ValueError, RuntimeError, OSError) as e:
        print("Failed to get data, giving up and restarting microcontroller\n", e)
        microcontroller.reset()
        continue

    train_color = read_color_input()

    elapsed_time = time.time() - last_data_send_time
    add_delay(elapsed_time)

    last_data_send_time = time.time()
    read_samples(train_color)
