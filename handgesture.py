# TechVidvan hand Gesture Recognizer
# https://techvidvan.com/tutorials/hand-gesture-recognition-tensorflow-opencv/

# import necessary packages

import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
import time

class HandGestureRecognizer:
    def __init__(self, capId, timeThreshold, confidence = 0.7, cap = None):
        # Initialize the webcam 
        if not cap == None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)
        self.timeThreshold = timeThreshold

        # initialize mediapipe
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1, min_detection_confidence=confidence)
        self.mpDraw = mp.solutions.drawing_utils

        # Load the gesture recognizer model
        self.model = load_model('handGestureDetect\mp_hand_gesture')

        # Load class names
        f = open('handGestureDetect\gesture.names', 'r')
        self.classNames = f.read().split('\n')
        f.close()

        self.currentClass = ""
        self.previousClass = ""
        self.time_without_change = 0
        self.last_update_time = time.time()

    def update_class(self, className):
        # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previousClass
        if className != self.previousClass:
            self.previousClass = className
            self.time_without_change = 0
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.time_without_change += time.time() - self.last_update_time

        self.last_update_time = time.time()
        # Wenn die Zeit ohne Änderung größer als 3 Sekunden ist, aktualisiere das Bild
        if self.time_without_change >= self.timeThreshold:
            # Hier kann der aktuelle Wert der Variable abgerufen werden
            current_value = className
            """"
            # Erstellen Sie ein Bild mit dem aktuellen Wert
            
            img = np.zeros((800, 1600, 3), np.uint8)
            cv2.putText(img, str(current_value), (50, 200 ), cv2.FONT_HERSHEY_SIMPLEX, 6, (255, 255, 255), 5)

            # Zeigen Sie das Bild im Fenster an
            cv2.imshow('Live-Anzeige', img)
            """
            # print(current_value)
            
            # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
            # self.last_update_time = time.time()
            self.currentClass = current_value
        
        # Speichere die letzte Aktualisierungszeit
        

    def run(self):
        # Read each frame from the webcam
        _, frame = self.cap.read()

        x, y, c = frame.shape

        # Flip the frame vertically
        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmark prediction
        result = self.hands.process(framergb)
        
        className = ''

        # post process the result
        if result.multi_hand_landmarks:
            landmarks = []
            for handslms in result.multi_hand_landmarks:
                for lm in handslms.landmark:
                    lmx = int(lm.x * x)
                    lmy = int(lm.y * y)

                    landmarks.append([lmx, lmy])

                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms, self.mpHands.HAND_CONNECTIONS)

                # Predict gesture
                prediction = self.model.predict([landmarks])
                
                classID = np.argmax(prediction)
                className = self.classNames[classID]

        # show the prediction on the frame
        cv2.putText(frame, className, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0,0,255), 2, cv2.LINE_AA)

        # Show the final output
        cv2.imshow("Output", frame)
        
        self.update_class(className)
        return self.currentClass
