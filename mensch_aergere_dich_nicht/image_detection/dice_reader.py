import cv2
import numpy as np
from collections import deque
import threading
from time import time
class DiceReader(threading.Thread):
    def __init__(self, cap):

        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.cap = cap

        self.frame = self.cap.frame

        self.prev_frame_time = 0
        self.new_frame_time = 0

        self.min_threshold = 10                      # these values are used to filter our detector.
        self.max_threshold = 200                     # they can be tweaked depending on the camera distance, camera angle, ...
        self.min_area = 100                          # ... focus, brightness, etc.
        self.min_circularity = 0.3
        self.min_inertia_ratio = 0.5 
        
        self.x , self.y, self.c = self.frame.shape
        self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)
        self.overlay = self.temp_overlay
 
        self.counter = 0                             # script will use a counter to handle FPS.
        self.readings = deque([0, 0], maxlen=10)     # lists are used to track the number of pips.
        self.display = deque([0, 0], maxlen=10)
        self.params = cv2.SimpleBlobDetector_Params()
        self.initialized = False
        
        self.eye_count = 0

    def blob_params(self):
                        # declare filter parameters.
        self.params.filterByArea = True
        self.params.filterByCircularity = True
        self.params.filterByInertia = True
        self.params.minThreshold =self.min_threshold
        self.params.maxThreshold = self.max_threshold
        self.params.minArea = self.min_area
        self.params.minCircularity = self.min_circularity
        self.params.minInertiaRatio = self.min_inertia_ratio

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
    def run(self):
        self.blob_params()
        detector = cv2.SimpleBlobDetector_create(self.params)
        while True:
            self.x , self.y, self.c = self.frame.shape
            self.temp_overlay = np.zeros((self.x, self.y, 3), np.uint8)

            self.frame = self.cap.frame
            keypoints = detector.detect(self.frame)
            self.temp_overlay = cv2.drawKeypoints(self.temp_overlay, keypoints, np.array([]), (0, 0, 255),
                                          cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            self.new_frame_time = time()
            fps = 1/(self.new_frame_time-self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time
            fps = int(fps)
            fps = str(fps)
            cv2.putText(self.temp_overlay, fps, (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

            if self.counter % 10 == 0:                                   # enter this block every 10 frames.
                reading = len(keypoints)                            # 'reading' counts the number of keypoints (pips).
                self.readings.append(reading)                            # record the reading from this frame.

            if self.readings[-1] == self.readings[-2] == self.readings[-3]:    # if the last 3 readings are the same...
                self.display.append(self.readings[-1])                    # ... then we have a valid reading.

            # if the most recent valid reading has changed, and it's something other than zero, then print it.
            if self.display[-1] != self.display[-2] and self.display[-1] != 0:
               self.eye_count = self.display[-1]

            self.counter += 1
            self.overlay = self.temp_overlay
            
            self.initialized = True
            if self.stopped():
                break