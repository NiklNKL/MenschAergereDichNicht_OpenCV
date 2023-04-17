import threading
from time import time
import cv2
from .fps import Fps

class VideoStream(threading.Thread):
    def __init__(self, cap_id, cap=None):
        
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.initialized = False

        self.cap_id = cap_id
        if cap is not None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(cap_id)

        _, self.temp_frame = self.cap.read()
        self.frame = self.temp_frame

        self.prev_frame_time = 0
        self.fps_tracker = Fps("VideoStream")
        self.stats = ""

    def stop(self):
        cv2.VideoCapture(self.cap_id).release()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
    def run(self):
        while True and not self.stopped():
            _, self.temp_frame = self.cap.read()

            self.temp_frame = self.fps_tracker.counter(self.temp_frame, self.prev_frame_time, name="Vid", corner=3)
            self.prev_frame_time = time()

            self.frame = self.temp_frame
            self.initialized = True
            self.stats = self.fps_tracker.stats
            if self.stopped():
                break