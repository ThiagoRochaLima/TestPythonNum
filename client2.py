#!/home/pi/mic_hat/.venv/bin/python

import RPi.GPIO as GPIO
import pyaudio
import pymumble_py3 as pymumble
from pymumble_py3.callbacks import PYMUMBLE_CLBK_CONNECTED as PCCONNECTED
from pymumble_py3.callbacks import PYMUMBLE_CLBK_DISCONNECTED as PCDISCONNECTED
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS

BUTTON = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN)

SERVERIP = ""  # server address
SERVERPORT = 0  # port number
NICKNAME = ""

from apa102_pi.driver import apa102

# Initialize the library and the strip
strip = apa102.APA102(num_led=3, global_brightness=20, mosi=10, sclk=11,
                      order='rgb')

# Turn off all pixels (sometimes a few light up when the strip gets power)
strip.clear_strip()

# Prepare a few individual pixels
# strip.set_pixel_rgb(LED #, Color Value)
strip.set_pixel_rgb(0, 0xFF0000)  # Red
strip.set_pixel_rgb(1, 0xFFFF00)  # Yellow
strip.set_pixel_rgb(2, 0x00FF00)  # Green


def user_count_is_1():
    strip.set_pixel_rgb(1, 0xFFFF00, 0)  # Yellow
    strip.show()


def user_count_is_2():
    strip.set_pixel_rgb(1, 0xFFFF00, 10)  # Yellow
    strip.show()


def user_is_sending_voice():
    strip.set_pixel_rgb(2, 0x00FF00, 100)  # Green
    strip.show()


def user_is_not_sending_voice():
    strip.set_pixel_rgb(2, 0x00FF00, 0)  # Green
    strip.show()


def device_is_connected_to_the_server():
    strip.set_pixel_rgb(0, 0xFF0000, 10)  # Red
    strip.show()


def device_is_disconnected_from_the_server():
    strip.set_pixel_rgb(0, 0xFF0000, 0)  # Red
    strip.show()


# Connection details for mumble server.
pwd = ""  # password
server = SERVERIP  # server address
nick = NICKNAME
port = SERVERPORT  # port number
RESPEAKER_INDEX = 1

# pyaudio set up
CHUNK = 512  # 1024
FORMAT = pyaudio.paInt16  # pymumble soundchunk.pcm is 16 bits
CHANNELS = 1
RATE = 48000  # pymumble soundchunk.pcm is 48000Hz

p = pyaudio.PyAudio()

input_stream = p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      input=True,  # enable both talk
                      frames_per_buffer=CHUNK)

output_stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True,  # and listen
                       frames_per_buffer=CHUNK,
                       output_device_index=RESPEAKER_INDEX)


# mumble client set up
def sound_received_handler(user, soundchunk):
    """ play sound received from mumble server upon its arrival """
    output_stream.write(soundchunk.pcm)


# Spin up a client and connect to mumble server
mumble = pymumble.Mumble(server, nick, password=pwd, port=port, reconnect=True)
# set up callback called when PCS event occurs
mumble.callbacks.set_callback(PCS, sound_received_handler)
mumble.callbacks.set_callback(PCCONNECTED, device_is_connected_to_the_server)
mumble.callbacks.set_callback(PCDISCONNECTED, device_is_disconnected_from_the_server)
mumble.set_receive_sound(1)  # Enable receiving sound from mumble server
mumble.start()
mumble.is_ready()  # Wait for client is ready

# capturing sound and sending it to mumble server when button is pressed
try:
    while True:
        state = GPIO.input(BUTTON)
        user_count = mumble.users.count()
        if user_count == 2:
            user_count_is_2()
        else:
            user_count_is_1()
        if not state:
            user_is_sending_voice()
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            mumble.sound_output.add_sound(data)
        else:
            user_is_not_sending_voice()

except KeyboardInterrupt:
    print("\nCtrl+C detected. Exiting...")
    print("Cleaning up resources.")
    # close the stream and pyaudio instance
    strip.cleanup()
    input_stream.stop_stream()
    input_stream.close()
    p.terminate()
