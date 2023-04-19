import cv2
import numpy as np
from collections import deque
import threading
from time import time, sleep
from utilities import Fps
class DiceReader(threading.Thread):
    def __init__(self, cap, time_threshold=2):

        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.cap = cap

        self.frame = self.cap.frame

        self.prev_frame_time = 0
        self.fps_tracker = Fps("DiceReader")
        self.stats = ""

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

        # Threshold on how long a gesture or a count needs to stay the same
        self.time_threshold = time_threshold

        # Variables used for class update
        self.current_eye_count = 0
        self.previous_eye_count = 0
        self.time_without_change = 0
        self.last_update_time = time()
        
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

    def update_eye_count(self, eye_count):
    # Wenn sich der Klassenname geändert hat, setze die Zeit ohne Änderung auf 0 zurück und aktualisiere previous_class
        if eye_count != self.previous_eye_count:
            self.previous_eye_count = eye_count
            self.time_without_change = 0
            if eye_count == 0:
                self.current_eye_count = eye_count
        else:
            # Andernfalls erhöhe die Zeit ohne Änderung um die vergangene Zeit seit dem letzten Update
            self.time_without_change += time() - self.last_update_time

        self.last_update_time = time()
        # Wenn die Zeit ohne Änderung größer als time_threshold Sekunden ist, aktualisiere das Bild
        if self.time_without_change >= self.time_threshold:
            # Hier kann der aktuelle Wert der Variable abgerufen werden
            current_value = eye_count
            # Setze die letzte Aktualisierungszeit auf die aktuelle Zeit
            # self.last_update_time = time.time()
            self.current_eye_count = current_value
            
            # Speichere die letzte Aktualisierungszeit

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
            max_x = 0
            max_y = 0
            min_x = self.temp_overlay.shape[1]
            min_y = self.temp_overlay.shape[0]
            if len(keypoints) > 0:
                for keypoint in keypoints:
                    self.temp_overlay = cv2.circle(self.temp_overlay, (int(keypoint.pt[0]),int(keypoint.pt[1])), int(keypoint.size*0.90), (255,0,0), 4)
                    if keypoint.pt[0] > max_x:
                        max_x = keypoint.pt[0] + keypoint.size
                    elif keypoint.pt[0] < min_x:
                        min_x = keypoint.pt[0] - keypoint.size
                    if keypoint.pt[1] > max_y:
                        max_y = keypoint.pt[1] + keypoint.size
                    elif keypoint.pt[1] < min_y:
                        min_y = keypoint.pt[1] - keypoint.size
                try:
                    if len(keypoints) > 1:
                        self.temp_overlay = cv2.rectangle(self.temp_overlay, (int(max_x), int(max_y)), (int(min_x), int(min_y)), (0, 255, 0),2)
                        self.temp_overlay = cv2.putText(self.temp_overlay, f"Dice: {len(keypoints)}" ,(int(min_x), int(min_y-30)), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2, cv2.LINE_AA)
                except Exception:
                    pass
            
            self.temp_overlay = self.fps_tracker.counter(self.temp_overlay, self.prev_frame_time, name="Dice", corner=2)
            self.prev_frame_time = time()
            
            self.eye_count = len(keypoints)
            if self.eye_count <=6:
                self.update_eye_count(self.eye_count)

            self.temp_overlay = cv2.putText(self.temp_overlay, f"Current Dice: {len(keypoints)}" ,(10, int(self.x-self.x*0.025)), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 1, cv2.LINE_AA)
            self.counter += 1
            self.overlay = self.temp_overlay
            
            self.initialized = True
            self.stats = self.fps_tracker.stats
            if self.stopped(): 
                break