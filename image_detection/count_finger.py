# TechVidvan hand Gesture Recognizer
# https://techvidvan.com/tutorials/hand-gesture-recognition-tensorflow-opencv/

# import necessary packages

import cv2
import mediapipe as mp
from time import time


class FingerCounter:
    def __init__(self, capId, timeThreshold, confidence = 0.7, cap = None):
        # Initialize the webcam 
        if not cap == None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)
        self.timeThreshold = timeThreshold

        # initialize mediapipe
        self.mpHands = mp.solutions.hands
        self.finger = self.mpHands.Hands(max_num_hands=2, min_detection_confidence=confidence)
        self.mpDraw = mp.solutions.drawing_utils
        self.currentCount = 0
        self.previousCount = 0
        self.time_without_change = 0
        self.last_update_time = time()

    def countFingers(self, results):
    
        # Initialize a dictionary to store the count of fingers of both hands.
        count = 0
        
        # Store the indexes of the tips landmarks of each finger of a hand in a list.
        fingers_tips_ids = [self.mpHands.HandLandmark.INDEX_FINGER_TIP, self.mpHands.HandLandmark.MIDDLE_FINGER_TIP,
                            self.mpHands.HandLandmark.RING_FINGER_TIP, self.mpHands.HandLandmark.PINKY_TIP]
        
        # Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
        fingers_statuses = {'RIGHT_THUMB': False, 'RIGHT_INDEX': False, 'RIGHT_MIDDLE': False, 'RIGHT_RING': False,
                            'RIGHT_PINKY': False, 'LEFT_THUMB': False, 'LEFT_INDEX': False, 'LEFT_MIDDLE': False,
                            'LEFT_RING': False, 'LEFT_PINKY': False}
        
        if results.multi_handedness is not None:
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
                        count += 1
                
                # Retrieve the y-coordinates of the tip and mcp landmarks of the thumb of the hand.
                thumb_tip_x = hand_landmarks.landmark[self.mpHands.HandLandmark.THUMB_TIP].x
                thumb_mcp_x = hand_landmarks.landmark[self.mpHands.HandLandmark.THUMB_TIP - 2].x
                
                # Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
                if (hand_label=='Right' and (thumb_tip_x < thumb_mcp_x)) or (hand_label=='Left' and (thumb_tip_x > thumb_mcp_x)):
                    
                    # Update the status of the thumb in the dictionary to true.
                    fingers_statuses[hand_label.upper()+"_THUMB"] = True
                    
                    # Increment the count of the fingers up of the hand by 1.
                    count += 1
        
        # Return the output image, the status of each finger and the count of the fingers up of both hands.
        return count
    
    def update_count(self, count):
        # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previousClass
        if count != self.previousCount:
            self.previousCount = count
            self.time_without_change = 0
            if count == 0:
                self.currentCount = count
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.time_without_change += time() - self.last_update_time

        self.last_update_time = time()
        # Wenn die Zeit ohne Änderung größer als timeThreshold Sekunden ist, aktualisiere das Bild
        if self.time_without_change >= self.timeThreshold:
            # Hier kann der aktuelle Wert der Variable abgerufen werden
            current_value = count
            # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
            # self.last_update_time = time.time()
            self.currentClass = current_value
        
        # Speichere die letzte Aktualisierungszeit

    def run(self):
        # Read each frame from the webcam
        _, frame = self.cap.read()

        # Flip the frame vertically
        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmark prediction
        result = self.finger.process(framergb)

        count = 0

        # post process the result
        if result.multi_hand_landmarks:
            for handslms in result.multi_hand_landmarks:
                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms, self.mpHands.HAND_CONNECTIONS)
                # Predict gesture
            count = self.countFingers(result)

        # show the prediction on the frame
        cv2.putText(frame, "Count: " + str(count), (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,0,255), 2, cv2.LINE_AA)

        # Show the final output
        # UiHandler.update(gestureFrame = frame)
        # cv2.imshow("Output", frame)
        #self.update_count(count)
        return count
