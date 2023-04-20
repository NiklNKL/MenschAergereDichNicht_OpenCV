from time import time
import cv2
import numpy as np

class Fps():
    '''Shows the frames per seconds for the video-streams and adds performance stats

    This module is initialized in every video stream to track the performance
    of each videostream.
    '''

    def __init__(self, name):
        '''Initializes the Fps class
        
        Initializes all the needed global variables.

        Args:
            name: takes a name that is displayed in the terminal
        '''

        self.fps_array = np.array([])
        self.average_fps = 0
        self.min_fps = 0
        self.max_fps = 0
        self.fps_array_sort = np.array([])
        self.stats = ""
        self.name = name
        self.debug = False
    
    def counter(self,frame, prev_frame_time, name=None, corner = 1):
        '''This method counts and displays the fps in the frame.

        Args:
            frame: takes a video frame
            prev_frame_time: duration of the last/previous run through
            name: the name that is displayed in the UI
            corner: an id in which corner the fps count should be displayed
        '''
        #sets the name if name=none
        if name is None:
            name = "NAN"
        name = name[:4]

        #takes the shape of the frame to calculate the position and size of the rectangle
        #for the fps counter according to the location set by the corner id
        y,x,c = frame.shape
        font_scale = x/1920
        if corner == 1:
            pos_x = int(0+(x*0.005))
            pos_y = int(0+(y*0.06))
            rec_start = (0,0)
            rec_end = (int(0+(x*0.06)), int(0+(y*0.07)))
        elif corner == 2:
            pos_x = int(x-(x*0.04))
            pos_y = int(0+(y*0.06))
            rec_start = (x,0)
            rec_end = (int(x-(x*0.05)), int(0+(y*0.07)))
        elif corner == 3:
            pos_x = int(0+(x*0.005))
            pos_y = int(y-(y*0.005))
            rec_start = (0,y)
            rec_end = (int(0+(x*0.06)), int(y-(y*0.07)))
        elif corner == 4:
            pos_x = int(x-(x*0.03))
            pos_y = int(y-(y*0.005))
            rec_start = (x,y)
            rec_end = (int(x-(x*0.04)), int(y-(y*0.07)))
        
        #sets the position of the text
        text_pos_y = int(pos_y - y*0.03)

        #gets new time and calculates the fps
        new_frame_time = time()
        fps = 1/(new_frame_time-prev_frame_time)
        fps = int(fps)

        #writes the calculated fps for each run through 
        #in an array to calculate the min, max and average fps
        #displays the stats in the terminal
        self.fps_array = np.append(self.fps_array, fps)
        self.average_fps = np.mean(self.fps_array)
        self.fps_array_sort = np.sort(self.fps_array)
        if self.fps_array_sort.size > 1: 
            self.min_fps = self.fps_array_sort[1]
        self.max_fps = np.max(self.fps_array)
        self.stats = f"# {self.name} FPS Stats: Average: {self.average_fps:.3f}, Min: {int(self.min_fps)}, Max: {int(self.max_fps)}"

        #draws the fps counter with the text on the frame and returns the final frame
        fps = str(fps)
        if self.debug:
            frame = cv2.rectangle(frame, rec_start, rec_end, (255,255,255),-1)
            frame = cv2.putText(frame, fps, (pos_x, pos_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale*1, (0, 0, 255), 1, cv2.LINE_AA)
            frame = cv2.putText(frame, name + ":", (pos_x, text_pos_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale*1, (0, 0, 255), 1, cv2.LINE_AA)
        return frame