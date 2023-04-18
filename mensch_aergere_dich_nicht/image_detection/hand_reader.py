# TechVidvan hand Gesture Recognizer
# https://techvidvan.com/tutorials/hand-gesture-recognition-tensorflow-opencv/

# import necessary packages
import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
from time import time, sleep
import threading
from utilities import Fps

class HandReader(threading.Thread):
    def __init__(self, timeThreshold, cap, confidence = 0.7, video_feed = "gesture"):
        
        threading.Thread.__init__(self)
        # Initialising of the videocapture
        self.cap = cap

        self.frame = self.cap.frame

        self.x , self.y, self.c = self.frame.shape

        self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)
        self.overlay = self.temp_overlay

        # Variable for gesture or counter stream
        self.video_feed = video_feed

        # initialize mediapipe
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1, min_detection_confidence=confidence)
        self.finger = self.mpHands.Hands(max_num_hands=2, min_detection_confidence=confidence)
        self.mpDraw = mp.solutions.drawing_utils

        # Load the gesture recognizer model
        self.model = load_model('mensch_aergere_dich_nicht/resources/models/handGestureDetect/mp_hand_gesture')

        # Load class names
        f = open('mensch_aergere_dich_nicht/resources/models/handGestureDetect/gesture.names', 'r')
        self.classNames = f.read().split('\n')
        f.close()

        #### Everthing needed for updating the gesture/count ####

        # Threshold on how long a gesture or a count needs to stay the same
        self.timeThreshold = timeThreshold

        # Variables used for class update
        self.currentClass = ""
        self.previousClass = ""
        self.time_without_change = 0
        self.last_update_time = time()

        # Variables used for count update
        self.currentCount = ''
        self.previousCount = ''
        self.count_time_without_change = 0
        self.count_last_update_time = time()

        self.prev_frame_time = 0
        self.fps_tracker = Fps("HandReader")
        self.stats = ""

        self.initialized = False

        self._stop_event = threading.Event()

    def countFingers(self, results):
    
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
        if results.multi_handedness is not None:
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
            
            # Return the output image, the status of each finger and the count of the fingers up of both hands.
        return count, fingers_statuses

    def annotate(self, image, results, fingers_statuses, count):
        '''
        This function will draw an appealing visualization of each fingers up of the both hands in the image.
        Args:
            image:            The image of the hands on which the counted fingers are required to be visualized.
            results:          The output of the hands landmarks detection performed on the image of the hands.
            fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands. 
            count:            A dictionary containing the count of the fingers that are up, of both hands.
            display:          A boolean value that is if set to true the function displays the resultant image and 
                            returns nothing.
        Returns:
            output_image: A copy of the input image with the visualization of counted fingers.
        '''
        
        # Get the height and width of the input image.
        width = self.y
        
        # Create a copy of the input image.
        output_image = image.copy()
        
        # Select the images of the hands prints that are required to be overlayed.
        ########################################################################################################################
        
        # Initialize a dictionaty to store the images paths of the both hands.
        # Initially it contains red hands images paths. The red image represents that the hand is not present in the image. 
        HANDS_IMGS_PATHS = {'LEFT': ["mensch_aergere_dich_nicht/resources/images/finger/left_hand_not_detected.png"], 'RIGHT': ['mensch_aergere_dich_nicht/resources/images/finger/right_hand_not_detected.png']}
        
        # Check if there is hand(s) in the image.
        if results.multi_hand_landmarks:
            
            # Iterate over the detected hands in the image.
            for hand_index, hand_info in enumerate(results.multi_handedness):
                
                # Retrieve the label of the hand.
                hand_label = hand_info.classification[0].label
                
                # Update the image path of the hand to a green color hand image.
                # This green image represents that the hand is present in the image. 
                HANDS_IMGS_PATHS[hand_label.upper()] = ['mensch_aergere_dich_nicht/resources/images/finger/'+hand_label.lower()+'_hand_detected.png']
                
                # Check if all the fingers of the hand are up/open.
                if count[hand_label.upper()] == 5:
                    
                    # Update the image path of the hand to a hand image with green color palm and orange color fingers image.
                    # The orange color of a finger represents that the finger is up.
                    HANDS_IMGS_PATHS[hand_label.upper()] = ['mensch_aergere_dich_nicht/resources/images/finger/'+hand_label.lower()+'_all_fingers.png']
                
                # Otherwise if all the fingers of the hand are not up/open.
                else:
                    
                    # Iterate over the fingers statuses of the hands.
                    for finger, status in fingers_statuses.items():
                        
                        # Check if the finger is up and belongs to the hand that we are iterating upon.
                        if status == True and finger.split("_")[0] == hand_label.upper():
                            
                            # Append another image of the hand in the list inside the dictionary.
                            # This image only contains the finger we are iterating upon of the hand in orange color.
                            # As the orange color represents that the finger is up.
                            HANDS_IMGS_PATHS[hand_label.upper()].append('mensch_aergere_dich_nicht/resources/images/finger/'+finger.lower()+'.png')
        
        ########################################################################################################################
        
        # Overlay the selected hands prints on the input image.
        ########################################################################################################################
        
        # Iterate over the left and right hand.
        for hand_index, hand_imgs_paths in enumerate(HANDS_IMGS_PATHS.values()):
            
            # Iterate over the images paths of the hand.
            for img_path in hand_imgs_paths:
                
                # Read the image including its alpha channel. The alpha channel (0-255) determine the level of visibility. 
                # In alpha channel, 0 represents the transparent area and 255 represents the visible area.
                hand_imageBGRA = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                hand_imageBGRA = cv2.resize(hand_imageBGRA, (100,100), interpolation=cv2.INTER_LINEAR)
                
                # Retrieve all the alpha channel values of the hand image. 
                alpha_channel = hand_imageBGRA[:,:,-1]
                
                # Retrieve all the blue, green, and red channels values of the hand image.
                # As we also need the three-channel version of the hand image. 
                hand_imageBGR  = hand_imageBGRA[:,:,:-1]
                
                # Retrieve the height and width of the hand image.
                hand_height, hand_width, _ = hand_imageBGR.shape

                # Retrieve the region of interest of the output image where the handprint image will be placed.
                ROI = output_image[30 : 30 + hand_height,
                                (hand_index * width//2) + width//12 : ((hand_index * width//2) + width//12 + hand_width)]
                
                # Overlay the handprint image by updating the pixel values of the ROI of the output image at the 
                # indexes where the alpha channel has the value 255.
                ROI[alpha_channel==255] = hand_imageBGR[alpha_channel==255]

                # Update the ROI of the output image with resultant image pixel values after overlaying the handprint.
                output_image[30 : 30 + hand_height,
                            (hand_index * width//2) + width//12 : ((hand_index * width//2) + width//12 + hand_width)] = ROI
        
        return output_image

    def getGesture(self, result, frame):
        className = ""
        if result.multi_hand_landmarks:
            landmarks = []
            for handslms in result.multi_hand_landmarks:
                for lm in handslms.landmark:
                    # print(id, lm)
                    lmx = int(lm.x * self.x)
                    lmy = int(lm.y * self.y)

                    landmarks.append([lmx, lmy])

                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms, self.mpHands.HAND_CONNECTIONS)
            # Predict gesture in Hand Gesture Recognition project

            
            try:
                prediction = self.model([landmarks])
            except Exception:
                landmarks = np.expand_dims(np.stack(landmarks), axis=0)
                prediction = self.model(landmarks)

            
            classID = np.argmax(prediction)
            className = self.classNames[classID]
            # show the prediction on the frame
            cv2.putText(frame, "Gesture: " + className, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "Waiting for Gesture...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 2, cv2.LINE_AA)
        return className, frame
        
    def getFingers(self, result, frame):
        count = 0
        # post process the result
        if result.multi_hand_landmarks:
            for handslms in result.multi_hand_landmarks:
                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms,self.mpHands.HAND_CONNECTIONS,
                                        landmark_drawing_spec=self.mpDraw.DrawingSpec(color=(255,255,255),
                                                                                    thickness=2, circle_radius=2),
                                        connection_drawing_spec=self.mpDraw.DrawingSpec(color=(0,255,0),
                                                                                        thickness=2, circle_radius=2))
            count, fingers_statuses = self.countFingers(result)
            frame = self.annotate(frame, result,fingers_statuses, count)
            count = sum(count.values())
            # show the prediction on the frame
            cv2.putText(frame, "Count: " + str(count), (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "Waiting for Fingercount...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 2, cv2.LINE_AA)
        return count, frame

    def update_class(self, className):
    # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previousClass
        if className != self.previousClass:
            self.previousClass = className
            self.time_without_change = 0
            if className == '':
                self.currentClass = className
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.time_without_change += time() - self.last_update_time

        self.last_update_time = time()
        # Wenn die Zeit ohne Änderung größer als timeThreshold Sekunden ist, aktualisiere das Bild
        if self.time_without_change >= self.timeThreshold:
            # Hier kann der aktuelle Wert der Variable abgerufen werden
            current_value = className
            # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
            # self.last_update_time = time.time()
            self.currentClass = current_value

    def update_count(self, count):
    # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previousClass
        if count != self.previousCount:
            self.previousCount = count
            self.count_time_without_change = 0
            if count == 0:
                self.currentCount = count
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.count_time_without_change += time() - self.count_last_update_time

        self.count_last_update_time = time()
        # Wenn die Zeit ohne Änderung größer als timeThreshold Sekunden ist, aktualisiere das Bild
        if self.count_time_without_change >= self.timeThreshold:
            # Hier kann der aktuelle Wert der Variable abgerufen werden
            current_value = count
            # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
            # self.last_update_time = time.time()
            self.currentCount = current_value
            
            # Speichere die letzte Aktualisierungszeit
    
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


    def run(self):
        while True:
            # Initialize the webcam for Hand Gesture Recognition Python proje
            self.frame = self.cap.frame
            self.x , self.y, self.c = self.frame.shape

            self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)

            # # Flip the frame vertically
            # self.frame = cv2.flip(self.frame, 1)

            framergb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            # Get hand landmark prediction
            result = self.hands.process(framergb)
            fingerResult = self.finger.process(framergb)

            className = ''
            count = -1

            if self.video_feed == "gesture":
                className, self.temp_overlay = self.getGesture(result, self.temp_overlay)
                self.update_class(className)

                self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Hand", corner=2)
                self.prev_frame_time = time()
                
                cv2.putText(self.temp_overlay, "Detected Gesture: " + self.currentClass, (800, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0,0,255), 2, cv2.LINE_AA)
                
            elif self.video_feed == "counter":
                count, self.temp_overlay = self.getFingers(fingerResult, self.temp_overlay)
                self.update_count(count)

                self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Hand", corner=2)
                self.prev_frame_time = time()

                cv2.putText(self.temp_overlay, "Detected Count: " + str(self.currentCount), (800, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0,0,255), 2, cv2.LINE_AA)
            self.overlay = self.temp_overlay
            # UiHandler.update(handFrame = self.frame)
            self.initialized = True
            self.stats = self.fps_tracker.stats
            if self.stopped():
                break