# colorsensor-with-adafruit-io

This project controls a device that reads from a TCS34725 color sensor and pushes the data to Adafruit IO. The project is designed to gather training data in support of a Machine Learning class for a high school engineering class.

See https://io.adafruit.com/ and https://learn.adafruit.com/adafruit-color-sensors


## Project Overview

Students are learning how to program in Python. They have a Pico W loaded with CircuitPython. The task is to sort candy by color by designing a machine that can scan a piece of candy and then sort it into the correct bin. In code, they will observe the color data from their sensor manually and try to recognize colors using an if ladder.

As a class, they will then study machine learning. The instructor will provide this code for the input of training data and uploading datapoints to Adafruit IO. The class will then take the training data and use it to train TensorFlow to recognize colors. Then, they will see if the trained model can control their hardware to sort candy.


## Hardware

The project was developed using a Raspberry Pi Pico W connected to a TCS34725 on a breakout board and CircuitPython 8.x. To work more consistently, an enclosure should be built around the color sensor to shield it from stray light. Right now, there is a user prompt from the serial port. There could be buttons attached to allow training data to be input.

Colors to train:
- Red
- Purple
- Yellow
- Orange
- Green

## Function

When the user inputs the color to train, the data from the color sensor is read and recorded as a datapoint in the Adafruit IO stream along with the correct color input by the trainer.

The data is recorded as a string field in an Adafruit IO stream as a python dictionary. For example:

```
{'temperature': 2707, 'r' : 50, 'g': 12, 'b': 3, 'lux' : 102, 'color': 'red}
```

The idea is to then download the data and use it as input to train a Machine Learning model.
When I was developing this code I uploaded my data to: https://io.adafruit.com/ericzundel/feeds/colorsensor-training-data

## secrets.py

Some of the configuation is stored in a separate file according to convention. In the file `secrets.py` you should save the following data. Don't check this file into git for security reasons.

```
secrets = {
    'wifi_ssid': 'School Network',  # WiFi network name to connect to
    'wifi_password': 'password',    # Password to your network (if any)
    'aio_username' : 'hwhacker',    # Your AdafruitIO username
    'aio_key' : '0U812DEADBEEF',    # AdafruitIO API key. See the 'key' icon on the AdafruitIO home page
    'aio-colorsensor-feed-id' : 'colorsensor-training-data', # The name of your feed in Adafruit IO
}
```
