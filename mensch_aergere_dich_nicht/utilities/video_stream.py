import threading
import cv2

class VideoStream(threading.Thread):
    def __init__(self, cap_id):
        
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.initialized = False
        self.cap = cv2.VideoCapture(cap_id)

        _, self.frame = self.cap.read()

        self.cap_id = cap_id

    def stop(self):
        cv2.VideoCapture(self.cap_id).release()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
    
    def run(self):
        while True and not self.stopped():
            _, self.frame = self.cap.read()
            self.initialized = True
            if self.stopped():
                break