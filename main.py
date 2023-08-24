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
raspberry_pi_ip = "172.20.10.2"
url = f"http://{raspberry_pi_ip}:5000/process_photo"

try:
    speak("Motion detection is armed. Waiting for motion...")
    
    while True:
        if GPIO.input(PIR_PIN):
            speak("Motion detected!")
            
            # Capture a photo with the highest quality using fswebcam
            photo_filename = "captured_photo.jpg"
            subprocess.run(["fswebcam", "-r", "1920x1080", "--no-banner", photo_filename])
            speak("Photo captured.")
            
            # Prepare the data payload
            with open(photo_filename, "rb") as photo_file:
                files = {'file': (photo_filename, photo_file, 'image/jpeg')}
                
                speak("Sending the photo to the server.")
                response = requests.post(url, files=files)
                
            speak("Photo sent. Server response received.")