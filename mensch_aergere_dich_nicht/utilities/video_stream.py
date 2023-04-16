import threading
from time import time
import cv2

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
        self.new_frame_time = 0

    def stop(self):
        cv2.VideoCapture(self.cap_id).release()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
    def run(self):
        while True and not self.stopped():
            _, self.temp_frame = self.cap.read()
            self.new_frame_time = time()
            fps = 1/(self.new_frame_time-self.prev_frame_time)
            self.prev_frame_time = self.new_frame_time
            fps = int(fps)
            fps = str(fps)
            cv2.putText(self.temp_frame, fps, (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)
            self.frame = self.temp_frame
            self.initialized = True
            if self.stopped():
                break