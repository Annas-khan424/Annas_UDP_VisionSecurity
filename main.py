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
            # Print the response
            print("Response:", response.text)
            
            # Process the server response
            try:
                response_json = response.json()
                if "qr_code_data" in response_json:
                    qr_code_data = response_json["qr_code_data"]
                    if len(qr_code_data) > 0:
                        user_info = qr_code_data[0]
                        if "Name:" in user_info and "ID:" in user_info:
                            user_name = user_info.split("Name:")[1].split(",")[0].strip()
                            user_id = user_info.split("ID:")[1].split(",")[0].strip()
                            speak("Welcome, " + user_name + ". Your ID is " + user_id)
                        else:
                            print("Invalid QR code data format")
                            speak("Invalid QR code data format")
                    else:
                        print("No QR code data found")
                        speak("No QR code data found")
                elif "result" in response_json:
                    face_match_result = response_json["result"]
                    if "Face matches" in face_match_result:
                        user_name = face_match_result.split("with")[1].strip()
                        speak("Welcome, " + user_name[:-10])  # Remove "_photo.jpg" part
                    else:
                        print("Invalid photo: No face or multiple faces detected")
                        speak("Invalid photo: No face or multiple faces detected")
                elif "error" in response_json:
                    error_message = response_json["error"]
                    print(error_message)
                    speak(error_message)
                else:
                    print("Unexpected server response:", response.text)
            except Exception as e:
                print("Error processing server response:", str(e))
                speak("Error processing server response")

except KeyboardInterrupt:
    pass  # Exit gracefully on Ctrl+C
finally:
    GPIO.cleanup()
    if os.path.exists(photo_filename):
        os.remove(photo_filename)
        print("Temporary photo file deleted.")               
            