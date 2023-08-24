import time
import requests
import subprocess
import os
import pyttsx3
import RPi.GPIO as GPIO

# Initialize the GPIO pins
GPIO.setmode(GPIO.BCM)
PIR_PIN = 17  # Change to your chosen GPIO pin
GPIO.setup(PIR_PIN, GPIO.IN)

# Initialize the pyttsx3 engine
engine = pyttsx3.init()
# Function to speak the given text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Raspberry Pi IP and URL
raspberry_pi_ip = "192.168.1.2"
url = f"http://{raspberry_pi_ip}:5000/process_photo"