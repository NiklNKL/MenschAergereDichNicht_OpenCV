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
    def __init__(self, capId, timeThreshold, confidence = 0.5, cap = None):
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
        self.model = load_model('image_detection/handGestureDetect/mp_hand_gesture')

        # Load class names
        f = open('image_detection/handGestureDetect/gesture.names', 'r')
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
            if className == '':
                self.currentClass = className
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.time_without_change += time.time() - self.last_update_time

        self.last_update_time = time.time()
        # Wenn die Zeit ohne Änderung größer als timeThreshold Sekunden ist, aktualisiere das Bild
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

    def countFingers(self, image, results, draw=False):
        '''
        This function will count the number of fingers up for each hand in the image.
        Args:
            image:   The image of the hands on which the fingers counting is required to be performed.
            results: The output of the hands landmarks detection performed on the image of the hands.
            draw:    A boolean value that is if set to true the function writes the total count of fingers of the hands on the
                    output image.
            display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
        Returns:
            output_image:     A copy of the input image with the fingers count written, if it was specified.
            fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands.
            count:            A dictionary containing the count of the fingers that are up, of both hands.
        '''
        
        # Get the height and width of the input image.
        height, width, _ = image.shape
        
        # Create a copy of the input image to write the count of fingers on.
        output_image = image.copy()
        
        # Initialize a dictionary to store the count of fingers of both hands.
        count = {'RIGHT': 0, 'LEFT': 0}
        
        # Store the indexes of the tips landmarks of each finger of a hand in a list.
        fingers_tips_ids = [self.mpHands.HandLandmark.INDEX_FINGER_TIP, self.mpHands.HandLandmark.MIDDLE_FINGER_TIP,
                            self.mpHands.HandLandmark.RING_FINGER_TIP, self.mpHands.HandLandmark.PINKY_TIP]
        
        # Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
        fingers_statuses = {'RIGHT_THUMB': False, 'RIGHT_INDEX': False, 'RIGHT_MIDDLE': False, 'RIGHT_RING': False,
                            'RIGHT_PINKY': False, 'LEFT_THUMB': False, 'LEFT_INDEX': False, 'LEFT_MIDDLE': False,
                            'LEFT_RING': False, 'LEFT_PINKY': False}
        
        
        # Iterate over the found hands in the image.
        for hand_index, hand_info in enumerate(results.multi_handedness):
            
            # Retrieve the label of the found hand.
            hand_label = hand_info.classification[0].label
            
            # Retrieve the landmarks of the found hand.
            hand_landmarks =  results.multi_hand_landmarks[hand_index]
            
            # Iterate over the indexes of the tips landmarks of each finger of the hand.
            for tip_index in fingers_tips_ids:
                
                # Retrieve the label (i.e., index, middle, etc.) of the finger on which we are iterating upon.
                finger_name = tip_index.name.split("_")[0]
                
                # Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
                if (hand_landmarks.landmark[tip_index].y < hand_landmarks.landmark[tip_index - 2].y):
                    
                    # Update the status of the finger in the dictionary to true.
                    fingers_statuses[hand_label.upper()+"_"+finger_name] = True
                    
                    # Increment the count of the fingers up of the hand by 1.
                    count[hand_label.upper()] += 1
            
            # Retrieve the y-coordinates of the tip and mcp landmarks of the thumb of the hand.
            thumb_tip_x = hand_landmarks.landmark[self.mpHands.HandLandmark.THUMB_TIP].x
            thumb_mcp_x = hand_landmarks.landmark[self.mpHands.HandLandmark.THUMB_TIP - 2].x
            
            # Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
            if (hand_label=='Right' and (thumb_tip_x < thumb_mcp_x)) or (hand_label=='Left' and (thumb_tip_x > thumb_mcp_x)):
                
                # Update the status of the thumb in the dictionary to true.
                fingers_statuses[hand_label.upper()+"_THUMB"] = True
                
                # Increment the count of the fingers up of the hand by 1.
                count[hand_label.upper()] += 1
        
        # Check if the total count of the fingers of both hands are specified to be written on the output image.
        if draw:

            # Write the total count of the fingers of both hands on the output image.
            cv2.putText(output_image, " Total Fingers: ", (10, 25),cv2.FONT_HERSHEY_COMPLEX, 1, (20,255,155), 2)
            cv2.putText(output_image, str(sum(count.values())), (width//2-150,240), cv2.FONT_HERSHEY_SIMPLEX,
                        8.9, (20,255,155), 10, 10)

        # Check if the output image is specified to be displayed.
        else:

            # Return the output image, the status of each finger and the count of the fingers up of both hands.
            return output_image, fingers_statuses, count

    def run(self, UiHandler):
        # Read each frame from the webcam
        _, frame = self.cap.read()

        x, y, c = frame.shape

        # Flip the frame vertically
        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmark prediction
        result = self.hands.process(framergb)
        
        className = ''
        count = ""

        # post process the result
        if result.multi_hand_landmarks:
            landmarks = []
            for handslms in result.multi_hand_landmarks:
                for lm in handslms.landmark:
                    lmx = int(lm.x * x)
                    lmy = int(lm.y * y)

                    landmarks.append([lmx, lmy])

                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(image = frame, landmark_list = handslms,
                                      connections = self.mpHands.HAND_CONNECTIONS,
                                      landmark_drawing_spec=self.mpDraw.DrawingSpec(color=(255,255,255),
                                                                                   thickness=2, circle_radius=2),
                                      connection_drawing_spec=self.mpDraw.DrawingSpec(color=(0,255,0),
                                                                                     thickness=2, circle_radius=2))

                # Predict gesture
                prediction = self.model([landmarks])
                
                classID = np.argmax(prediction)
                className = self.classNames[classID]
            frame, fingers_statuses, count = self.countFingers(frame, result)

        # show the prediction on the frame
        cv2.putText(frame, className + " - " + str(count), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0,0,255), 2, cv2.LINE_AA)

        # Show the final output
        UiHandler.update(gestureFrame = frame)
        # cv2.imshow("Output", frame)
        
        self.update_class(className)
        return self.currentClass
