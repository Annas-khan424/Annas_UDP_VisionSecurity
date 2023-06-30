import threading
import cv2
import RPi.GPIO as GPIO
import time

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import os
#pubnub channel
PIR_channel="PIR-channel"
pnconfig = PNConfiguration()
pnconfig.publish_key = "sub-c-babca055-8ae8-4cbb-87e3-d1927bc7826a"
pnconfig.subscribe_key = "pub-c-7b7bf3ef-a5df-4ec8-9bb2-f70cc90f6c86"
pnconfig.user_id = "khan-machine"
pubnub = PubNub(pnconfig)


data={}
sensorList=["pir","buzzer","start_webcam"]


PIR_pin = 17
BUZZER_pin = 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(PIR_pin,GPIO.IN)#PIR
GPIO.setup(BUZZER_pin,GPIO.OUT)#Buzzer

pwm=GPIO.PWM(BUZZER_pin,500)
#pubnub channel
PIR_channel="PIR-channel"



# class PIR_pin:
#     pass
def start_webcam ():
cap = cv2.VideoCapture
while True:
    ret, img=cap.read()
    cv2.imshow('webcam', img)
    k=cv2.waitKey(10)
    if k==27:
        break;
cap.release()
cv2.destroyAllWindows


def motion_detection():
    data["alarm"] = False
    print("sensor started")
    trigger = False
    while True:
        if GPIO.input(PIR_pin):
            publishToPubNub(PIR_channel, {"motion": "yes"})
            print("motion detected")
            beep(4)

            data["motion"] = 1
        elif trigger:
            data["motion"] = 0
            publishToPubNub(PIR_channel, {"motion": "no"})
            trigger = False
            print("no motion")
        time.sleep(1)

        if motion_detection() == True:
            # call to start webcam

            web_cam = threading.Thread(target=start_webcam(True))
            web_cam.start()
            web_cam.join()

        else:
            pubnubmsg = "not in range"
            print(pubnubmsg)


def beep(repeat):
    for i in range(0, repeat):
        for pulse in range(60):
            pwm.start(100)
            time.sleep(0.001)
            pwm.stop()
            time.sleep(0.001)
        time.sleep(0.02)


def publishToPubNub(channel, message):
    pubnub.publish().channel(PIR_channel).message(message).pn_async(my_publish_callback)


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():

        pass  # Message successfully published to specified channel.
    else:
        pass  # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];


class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            pass  # This event happens when radio / connectivity is lost

        elif status.category == PNStatusCategory.PNConnectedCategory:
            # Connect event. You can do stuff like publish, and know you'll get it.
            # Or just use the connected event to confirm you are subscribed for
            # UI / internal notifications, etc

            print("MySubscribeCallback")


        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.

    def message(self, pubnub, message):
        # Handle new message stored in message.message
        try:
            print("def message")
            msg = message.message
            key = list(msg.keys())
            if (key[0]) == "event":
                self.handleEvent(msg)
            print(message.message)
        except Exception as e:
            print("Received:", message.message)
            print(e)
            pass

    def handleEvent(self, msg):
        global data
        eventData = msg["event"]
        key = list(eventData.keys())
        print(key)
        if key[0] in sensorList == "motion":
            if eventData[key[0]] is True:
                data["alarm"] = True
            elif eventData[key[0]] is False:
                data["alarm"] = False


if __name__ == "__main__":
    pir_thread=threading.Thread(target=motion_detection)
    pir_thread.start()
    web_camera_thread=threading.Thread(target=start_webcam(True))

    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels(PIR_channel).execute()


