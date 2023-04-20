# TechVidvan hand Gesture Recognizer
# https://techvidvan.com/tutorials/hand-gesture-recognition-tensorflow-opencv/

import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
from time import time
import threading
from utilities import Fps

class HandReader(threading.Thread):
    '''Detects hand(s) and predicts gesture or counts fingers.

    This module takes a frame from the VideoStream thread,
    analysies it with a hand recognition model from MediaPipe,
    and interprets the found keypoints as a gesture with the
    help of a pretrained keras model, or as the number of fingers
    extruded for counting. Other classes can change the video_feed
    to change what it predicts. The result is saved in current_gesture
    and current_count.
    '''
    
    def __init__(self, cap, time_threshold = 2,  confidence = 0.7, video_feed = "gesture"):
        ''' Initializes the HandReader class as a thread.

        Initializes all the needed global variables. Also sets up
        the method to stop the thread. Other variables are for tracking fps,
        hand recognition with MediaPipe, Keras or update function etc.

        Args:
            cap:            takes in a VideoStream object to read frames from
            time_threshold: sets time a count needs to stay the same for it to update
            confidence:     changes the calulation effords of MediaPipe and tweaks performance
            video_feed:     tells the model either predict gesture or finger count
        '''

        # Methods needed for multithreading start and stop
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        # Flag if the class already had one successfull run
        self.initialized = False

        # Everthing about the video frame
        self.cap = cap
        self.frame = self.cap.frame
        self.x , self.y, self.c = self.frame.shape

        # Creation of overlay with same size as frame
        self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)

        # Needed temp so that overlay only changes after a full run and not constantly
        self.overlay = self.temp_overlay

        # initialize mediapipe models, one for gestures with 1 hand, the other for finger count with 2 hands
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1, min_detection_confidence=confidence)
        self.finger = self.mpHands.Hands(max_num_hands=2, min_detection_confidence=confidence)
        self.mpDraw = mp.solutions.drawing_utils

        # Load the gesture recognizer model
        self.model = load_model('mensch_aergere_dich_nicht/resources/models/handGestureDetect/mp_hand_gesture')

        # Load gesture names
        f = open('mensch_aergere_dich_nicht/resources/models/handGestureDetect/gesture.names', 'r')
        self.gestureNames = f.read().split('\n')
        f.close()

        # Variable for gesture or counter stream
        self.video_feed = video_feed

        # Threshold on how long a gesture or a count needs to stay the same
        self.time_threshold = time_threshold

        # Variables used for gesture update
        self.current_gesture = ""
        self.previous_gesture = ""
        self.gesture_time_without_change = 0
        self.gesture_last_update_time = time()

        # Variables used for finger count update
        self.current_count = 0
        self.previous_count = 0
        self.count_time_without_change = 0
        self.count_last_update_time = time()

        # Variables needed for performance testing
        self.prev_frame_time = 0
        self.fps_tracker = Fps("HandReader")
        self.stats = ""

    def count_fingers(self, results):
        '''Counts the stretched out fingers by comparing keypoint coordinates.

        Counts fingers for every hand idividualy by comparing the y-coordinates
        of fingertips and the middle of the finger. If the fingertip coordinate
        is lower, it assumes that the finger is streched out. Thumbs are calculated
        with the x-coordinates.

        Args:
            results:    takes the result of the hand keypoint detection from MediaPipe

        Returns:
            count:              count of fingers streched out
            fingers_statuses:   dictonary of booleans, if a specific finger is streched out or not
        '''
    
        # Initialize a dictionary to store the count of fingers of both hands.
        count = {'RIGHT': 0, 'LEFT': 0}
        
        # Store the indexes of the tips landmarks of each finger of a hand in a list.
        fingers_tips_ids = [self.mpHands.HandLandmark.INDEX_FINGER_TIP, self.mpHands.HandLandmark.MIDDLE_FINGER_TIP,
                            self.mpHands.HandLandmark.RING_FINGER_TIP, self.mpHands.HandLandmark.PINKY_TIP]
        
        # Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
        fingers_statuses = {'RIGHT_THUMB': False, 'RIGHT_INDEX': False, 'RIGHT_MIDDLE': False, 'RIGHT_RING': False,
                            'RIGHT_PINKY': False, 'LEFT_THUMB': False, 'LEFT_INDEX': False, 'LEFT_MIDDLE': False,
                            'LEFT_RING': False, 'LEFT_PINKY': False}
        
        # Iterate over the found hands in the frame.
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
            
            # Return the output frame, the status of each finger and the count of the fingers up of both hands.
        return count, fingers_statuses

    def annotate(self, frame, results, fingers_statuses, count):
        '''This function will draw an appealing visualization of each fingers up of the both hands in the frame.

        This method takes information about the fingers and puts images on the frame
        fitting to the specific streched out fingers. The pictures are placed in an
        defined region of interest.

        Args:
            frame:            The frame of the hands on which the counted fingers are required to be visualized.
            results:          The output of the hands landmarks detection performed on the frame of the hands.
            fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands. 
            count:            A dictionary containing the count of the fingers that are up, of both hands.

        Returns:
            output_frame: A copy of the input frame with the visualization of counted fingers.
        '''
        
        # Get the height and width of the input frame.
        width = self.y
        
        # Create a copy of the input frame.
        output_frame = frame.copy()
        
        # Select the frames of the hands prints that are required to be overlayed.
        ########################################################################################################################
        
        # Initialize a dictionaty to store the frames paths of the both hands.
        # Initially it contains red hands frames paths. The red frame represents that the hand is not present in the frame. 
        HANDS_IMGS_PATHS = {'LEFT': ["mensch_aergere_dich_nicht/resources/frames/finger/left_hand_not_detected.png"], 'RIGHT': ['mensch_aergere_dich_nicht/resources/frames/finger/right_hand_not_detected.png']}
        
        # Check if there is hand(s) in the frame.
        if results.multi_hand_landmarks:
            
            # Iterate over the detected hands in the frame.
            for hand_index, hand_info in enumerate(results.multi_handedness):
                
                # Retrieve the label of the hand.
                hand_label = hand_info.classification[0].label
                
                # Update the frame path of the hand to a green color hand frame.
                # This green frame represents that the hand is present in the frame. 
                HANDS_IMGS_PATHS[hand_label.upper()] = ['mensch_aergere_dich_nicht/resources/frames/finger/'+hand_label.lower()+'_hand_detected.png']
                
                # Check if all the fingers of the hand are up/open.
                if count[hand_label.upper()] == 5:
                    
                    # Update the frame path of the hand to a hand frame with green color palm and orange color fingers frame.
                    # The orange color of a finger represents that the finger is up.
                    HANDS_IMGS_PATHS[hand_label.upper()] = ['mensch_aergere_dich_nicht/resources/frames/finger/'+hand_label.lower()+'_all_fingers.png']
                
                # Otherwise if all the fingers of the hand are not up/open.
                else:
                    
                    # Iterate over the fingers statuses of the hands.
                    for finger, status in fingers_statuses.items():
                        
                        # Check if the finger is up and belongs to the hand that we are iterating upon.
                        if status == True and finger.split("_")[0] == hand_label.upper():
                            
                            # Append another frame of the hand in the list inside the dictionary.
                            # This frame only contains the finger we are iterating upon of the hand in orange color.
                            # As the orange color represents that the finger is up.
                            HANDS_IMGS_PATHS[hand_label.upper()].append('mensch_aergere_dich_nicht/resources/frames/finger/'+finger.lower()+'.png')
        
        ########################################################################################################################
        
        # Overlay the selected hands prints on the input frame.
        ########################################################################################################################
        
        # Iterate over the left and right hand.
        for hand_index, hand_imgs_paths in enumerate(HANDS_IMGS_PATHS.values()):
            
            # Iterate over the frames paths of the hand.
            for img_path in hand_imgs_paths:
                
                # Read the frame including its alpha channel. The alpha channel (0-255) determine the level of visibility. 
                # In alpha channel, 0 represents the transparent area and 255 represents the visible area.
                hand_frameBGRA = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                hand_frameBGRA = cv2.resize(hand_frameBGRA, (100,100), interpolation=cv2.INTER_LINEAR)
                
                # Retrieve all the alpha channel values of the hand frame. 
                alpha_channel = hand_frameBGRA[:,:,-1]
                
                # Retrieve all the blue, green, and red channels values of the hand frame.
                # As we also need the three-channel version of the hand frame. 
                hand_frameBGR  = hand_frameBGRA[:,:,:-1]
                
                # Retrieve the height and width of the hand frame.
                hand_height, hand_width, _ = hand_frameBGR.shape

                # Retrieve the region of interest of the output frame where the handprint frame will be placed.
                ROI = output_frame[10 : 10 + hand_height,
                                ((hand_index * width*3//4) + width//24) : (((hand_index * width*3//4) + width//24) + hand_width)]
                
                # Overlay the handprint frame by updating the pixel values of the ROI of the output frame at the 
                # indexes where the alpha channel has the value 255.
                ROI[alpha_channel==255] = hand_frameBGR[alpha_channel==255]

                # Update the ROI of the output frame with resultant frame pixel values after overlaying the handprint.
                output_frame[10 : 10 + hand_height,
                            ((hand_index * width*3//4) + width//24) : (((hand_index * width*3//4) + width//24) + hand_width)] = ROI
        
        return output_frame

    def get_gesture(self, result, frame):
        '''This function predicts the gesture and draws a hand sceleton on the given frame.

        It takes the output from keypoint detection of the MediaPipe,
        iterates through all keypoints and converts them into the right
        data for the keras model. It draws the keypoints onto the frame
        and predicts the gesture.

        Args:
            results:    The output of the hands landmarks detection performed on the frame of the hands.
            frame:      The frame of the hands on which the counted fingers are required to be visualized.

        Returns:
            gesture:    Name of predicted gesture.
            frame:      Input frame with the visualization of keypoints.
        '''
        # Initializes gesture variable
        gesture = ""

        # Iterates through all predicted hands
        if result.multi_hand_landmarks:
            landmarks = []

            # Iterates through all keypoints of one hand
            for handslms in result.multi_hand_landmarks:

                # Iterates through coordinates of keypoints and converts them with frame size
                for lm in handslms.landmark:
                    lmx = int(lm.x * self.x)
                    lmy = int(lm.y * self.y)

                    landmarks.append([lmx, lmy])

                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms, self.mpHands.HAND_CONNECTIONS)

            # Predict gesture in Hand Gesture Recognition project
            # Works on most pcs like that
            try:
                prediction = self.model([landmarks])

            # Sometimes the array must be edited before prediction
            except Exception:
                landmarks = np.expand_dims(np.stack(landmarks), axis=0)
                prediction = self.model(landmarks)

            # Gets gesture name from predicted id
            gestureID = np.argmax(prediction)
            gesture = self.gestureNames[gestureID]

            # Shows the prediction on the frame
            cv2.putText(frame, "Gesture: " + gesture, (10, int(self.x-self.x*0.025)), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 1, cv2.LINE_AA)
            
        # Waits for a hand to get detected
        else:
            cv2.putText(frame, "Waiting for Gesture...", (10, int(self.x-self.x*0.025)), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 1, cv2.LINE_AA)
            
        return gesture, frame
        
    def get_fingers(self, result, frame):
        '''This function counts the fingers and draws a hand sceleton on the given frame.

        It takes the output from keypoint detection of the MediaPipe and
        iterates through all keypoints.  It draws the keypoints onto the frame,
        counts the fingers and visualizes them.

        Args:
            result:     The output of the hands landmarks detection performed on the frame of the hands.
            frame:      The frame of the hands on which the counted fingers are required to be visualized.

        Returns:
            count:      Count of streched out fingers.
            frame:      Input frame with the visualization of keypoints.
        '''

        # Initializes count variable
        count = 0

        # Iterates through all predicted hands
        if result.multi_hand_landmarks:

            # Iterates through all keypoints of one hand
            for handslms in result.multi_hand_landmarks:

                # Drawing landmarks on frames
                self.mpDraw.draw_landmarks(frame, handslms,self.mpHands.HAND_CONNECTIONS,
                                        landmark_drawing_spec=self.mpDraw.DrawingSpec(color=(255,255,255),
                                                                                    thickness=2, circle_radius=2),
                                        connection_drawing_spec=self.mpDraw.DrawingSpec(color=(0,255,0),
                                                                                        thickness=2, circle_radius=2))
            # Counts fingers    
            count, fingers_statuses = self.count_fingers(result)

            # Puts hand images on frame
            frame = self.annotate(frame, result,fingers_statuses, count)

            # Calculates the total sum of both hands
            count = sum(count.values())

            # Shows the count on the frame
            cv2.putText(frame, "Count: " + str(count), (10, int(self.y-self.y*0.025)), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 1, cv2.LINE_AA)
            
        # Waits for a hand to get detected
        else:
            cv2.putText(frame, "Waiting for Fingercount...", (10, int(self.y-self.y*0.025)), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,0,255), 1, cv2.LINE_AA)
            
        return count, frame

    def update_gesture(self, gesture):
        '''Updates self.current_gesture with a time_threshold.

        Only updates the current gesture if gesture stayed
        the same for the time set in time_threshold.
        Resets time without change after change.

        Args:
            gesture: takes the latest predicted gesture
        '''
        # Checks if the gesture stayed the same or not
        if gesture != self.previous_gesture:    # If the gesture changed, it saves the new gesture 
            self.previous_gesture = gesture     # as the new previous one and resets the timer
            self.gesture_time_without_change = 0

            # If there is no prediction, it resets automatically
            if gesture == '':
                self.current_gesture = gesture
        else:
            # If nothing changed the time keeps getting increased
            self.gesture_time_without_change += time() - self.gesture_last_update_time
        
        self.gesture_last_update_time = time()

        # If the time_threshold is reached, current_gesture gets updated
        if self.gesture_time_without_change >= self.time_threshold:
            self.current_gesture = gesture

    def update_count(self, count):
        '''Updates self.current_count with a time_threshold.

        Only updates the current finger count if count stayed
        the same for the time set in time_threshold.
        Resets time without change after change.

        Args:
            count: takes the latest finger count
        '''
        # Checks if the count stayed the same or not
        if count != self.previous_count:    # If the count changed, it saves the new count 
            self.previous_count = count     # as the new previous one and resets the timer
            self.count_time_without_change = 0

            # If there is no count, it resets automatically
            if count == 0:
                self.current_count = count
        else:
            # If nothing changed the time keeps getting increased
            self.count_time_without_change += time() - self.count_last_update_time

        self.count_last_update_time = time()

        # If the time_threshold is reached, current_gesture gets updated
        if self.count_time_without_change >= self.time_threshold:
            self.current_count = count
            
    def stop(self):
        # Needed to stop the thread
        self._stop_event.set()

    def stopped(self):
        # Returns status of thread
        return self._stop_event.is_set()

    def run(self):
        '''Gets called by hand_thread.start() and runs all the logic.

        This method first predicts one or two hands,
        depending on the video_feed variable. After that it predicts
        or counts fingers, and checks if the result changed since the
        last one or not. It updates the overlay and saves its 
        performance benchmark.
        '''

        # While-Loop which only breaks if the game stops
        while True:

            # Loads the current frame of VideoStream
            self.frame = self.cap.frame
            self.x , self.y, self.c = self.frame.shape

            # Resets the last overlay
            self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)

            # Converts colors to RGB for the MediaPipe
            framergb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            
            # For gesture recognition
            if self.video_feed == "gesture":

                # Processes the frame with MediaPipe model
                result = self.hands.process(framergb)

                # Predicts gesture and draws keypoints
                gesture, self.temp_overlay = self.get_gesture(result, self.temp_overlay)
                
                # Updates global gesture
                self.update_gesture(gesture)

                # Tracks runtime with fps class
                self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Hand", corner=2)
                self.prev_frame_time = time()

            # For finger counting  
            elif self.video_feed == "counter":

                # Processes the frame with MediaPipe model
                fingerResult = self.finger.process(framergb)

                # Counts fingers and draws keypoints
                count, self.temp_overlay = self.get_fingers(fingerResult, self.temp_overlay)
                
                # Updates global count
                self.update_count(count)

                # Tracks runtime with fps class
                self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Hand", corner=2)
                self.prev_frame_time = time()

            # Updates the overlay to the new finished frame
            self.overlay = self.temp_overlay

            # Saves the current stats in the class
            self.stats = self.fps_tracker.stats

            # Flags the class the first time it completed a run
            if not self.initialized:
                self.initialized = True
            
            # Breaks the loop if the thread was stopped
            if self.stopped():
                break