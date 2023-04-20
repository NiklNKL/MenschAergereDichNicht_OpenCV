import threading
from time import time
import cv2
from .fps import Fps

class VideoStream(threading.Thread):
    '''Reads frames from camera

    This module reads frames from a camera device 
    for other classes to use.
    '''

    def __init__(self, cap_id, cap=None):
        ''' Initializes the VideoStream class as a thread.

        Initializes all the needed global variables. Also sets up
        the method to stop the thread. Other variables are for tracking fps
        and camera resolution.

        Args:
            cap_id: takes the id of a video capture device to read frames from it
            cap:    takes a cv2.VideoCapture object instead of the cap_id
        '''
        
        # Methods needed for multithreading start and stop
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        # Flag if the class already had one successfull run
        self.initialized = False

        # Chooses between given VideoCapture objekt or cap_id and own VideoCapture objekt
        self.cap_id = cap_id
        if cap is not None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(cap_id)
        
        # Reads and saves frame
        _, self.temp_frame = self.cap.read()
        self.frame = self.temp_frame

        # Reads camera resolution
        self.camera_resolution = self.frame.shape

        # Variables needed for performance testing
        self.prev_frame_time = 0
        self.fps_tracker = Fps("VideoStream")
        self.stats = ""

    def stop(self):
        # Releases capture device when thread is stopped
        cv2.VideoCapture(self.cap_id).release()

        # Needed to stop the thread
        self._stop_event.set()

    def stopped(self):
        # Returns status of thread
        return self._stop_event.is_set()
    
    def run(self):
        '''Gets called by cap.start() and runs all the logic.

        This method reads the current frame of capture device and
        updates its performance benchmark
        '''

        # While-Loop which only breaks if the game stops
        while True and not self.stopped():

            # Loads the current frame of capture device
            _, self.temp_frame = self.cap.read()

            # Used for Fps tracking and performance stat collection
            self.temp_frame = self.fps_tracker.counter(self.temp_frame, self.prev_frame_time, name="Vid", corner=3)
            self.prev_frame_time = time()

            # Updates the global frame to the new finished frame
            self.frame = self.temp_frame

            # Saves the current stats in the class
            self.stats = self.fps_tracker.stats

            # Flags the class the first time it completed a run
            if not self.initialized:
                self.initialized = True
            
            # Breaks the loop if the thread was stopped
            if self.stopped():
                break