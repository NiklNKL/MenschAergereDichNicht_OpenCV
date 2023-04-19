import cv2
import numpy as np
import threading
from time import time
from utilities import Fps

class DiceReader(threading.Thread):
    '''Detects dots in frame, counts them and draws circle and bounding box on overlay.

    This module takes a frame from the VideoStream thread,
    analysies it with a cv2.SimpleBlobDetector and counts
    all the found areas. It also draws circles around the 
    keypoints and a bounding box around all keypoints
    on a black frame with the same size as the input.
    It has an update function which limits how often the 
    detected count can change. The current_eye_count should
    be used by other classes.
    '''

    def __init__(self, cap, time_threshold=1):
        ''' Initializes the DiceReader class as a thread.

        Initializes all the needed global variables. Also sets up
        the method to stop the thread. Other variables are for tracking fps,
        cv2.SimpleBlobDetector params, update function etc.

        Args:
            cap: takes in a VideoStream object to read frames from
            time_threshold: sets time a count needs to stay the same for it to update
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

        # Params for cv2.SimpleBlobDetector
        self.params = cv2.SimpleBlobDetector_Params()
        self.min_threshold = 10                      # these values are used to filter our detector.
        self.max_threshold = 200                     # they can be tweaked depending on the camera distance, camera angle, ...
        self.min_area = 100                          # ... focus, brightness, etc.
        self.min_circularity = 0.3
        self.min_inertia_ratio = 0.5 

        # Threshold on how long a gesture or a count needs to stay the same
        self.time_threshold = time_threshold

        # Variables used for eye_count update
        self.current_eye_count = 0
        self.previous_eye_count = 0
        self.time_without_change = 0
        self.last_update_time = time()

        # Variables needed for performance testing
        self.prev_frame_time = 0
        self.fps_tracker = Fps("DiceReader")
        self.stats = ""

    def blob_params(self):
        '''Declares params.

        Declares all parameters of the cv2.SimpleBlobDetector
        and converts them into the right format
        '''
        self.params.filterByArea = True
        self.params.filterByCircularity = True
        self.params.filterByInertia = True
        self.params.minThreshold = self.min_threshold
        self.params.maxThreshold = self.max_threshold
        self.params.minArea = self.min_area
        self.params.minCircularity = self.min_circularity
        self.params.minInertiaRatio = self.min_inertia_ratio

    def update_eye_count(self, eye_count):
        '''Updates self.current_eye_count with a time_threshold.

        Only updates the current eye count if count stayed
        the same for the time set in time_threshold.
        Resets time without change after change.
        '''

        # Checks if the eye count stayed the same or not
        if eye_count != self.previous_eye_count:    # If the eye_count changed, it saves the new count 
            self.previous_eye_count = eye_count     # as the new previous one and resets the timer
            self.time_without_change = 0
            # if eye_count == 0:
            #     self.current_eye_count = eye_count
        else:
            # If nothing changed the time keeps getting increased
            self.time_without_change += time() - self.last_update_time

        self.last_update_time = time()

        # If the time_threshold is reached, current_eye_count gets updated
        if self.time_without_change >= self.time_threshold:
            self.current_eye_count =  eye_count
            
    def stop(self):
        # Needed to stop the thread
        self._stop_event.set()

    def stopped(self):
        # Returns if the thread is still alive or not
        return self._stop_event.is_set()
    
    def run(self):
        '''Gets called by dice_thread.start() and runs all the logic.

        This method first detects the dots, then counts them.
        After that, it draws cirlce and bounding boxes on an overlay.
        At the end it updates the current_eye_count and overlay and
        updates its performance benchmark
        '''
        
        # Creates the blob detector
        self.blob_params()
        detector = cv2.SimpleBlobDetector_create(self.params)

        # While-Loop which only breaks if the game stops
        while True:

            # Loads the current frame of VideoStream
            self.frame = self.cap.frame
            self.x , self.y, self.c = self.frame.shape
            
            # Resets the last overlay
            self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)
            
            # Initializes the basic coordinates for the bounding rectangle
            max_x = 0
            max_y = 0
            min_x = self.temp_overlay.shape[1]
            min_y = self.temp_overlay.shape[0]

            # Detects the actual dots and returns keypoints with different parameters
            keypoints = detector.detect(self.frame)

            # Calculates the actual eye_count
            eye_count = len(keypoints)

            # Draws circles and rectangles around keypoints
            if eye_count > 0:
                for keypoint in keypoints:

                    # Draws circles around the detected dots 
                    self.temp_overlay = cv2.circle(self.temp_overlay, (int(keypoint.pt[0]),int(keypoint.pt[1])), int(keypoint.size*0.70), (255,0,0), 4)

                    # Sorts the keypoint coordinates to get the top left and bottom right one
                    if keypoint.pt[0] > max_x:
                        max_x = keypoint.pt[0] + keypoint.size  # max right
                    elif keypoint.pt[0] < min_x:
                        min_x = keypoint.pt[0] - keypoint.size  # max left
                    if keypoint.pt[1] > max_y:
                        max_y = keypoint.pt[1] + keypoint.size  # max down
                    elif keypoint.pt[1] < min_y:
                        min_y = keypoint.pt[1] - keypoint.size  # max up

                # Tries to draw the rectangle around the keypoints if there is more than 1 keypoint       
                try:
                    if eye_count > 1:
                        self.temp_overlay = cv2.rectangle(self.temp_overlay, (int(max_x), int(max_y)), (int(min_x), int(min_y)), (0, 255, 0),2)
                        self.temp_overlay = cv2.putText(self.temp_overlay, f"Dice: {len(keypoints)}" ,(int(min_x), int(min_y-30)), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2, cv2.LINE_AA)
                except Exception:
                    pass
            
            # Used for Fps tracking and performance stat collection
            self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Dice", corner=2)
            self.prev_frame_time = time()
            
            # If only 6 or less dots are found, the current_eye_count can be updated
            if eye_count <=6:
                self.update_eye_count(eye_count)

            # Writes the current dice count to the bottom left of the screen
            self.temp_overlay = cv2.putText(self.temp_overlay, f"Current Dice: {eye_count}" ,(10, int(self.x-self.x*0.025)), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 1, cv2.LINE_AA)

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