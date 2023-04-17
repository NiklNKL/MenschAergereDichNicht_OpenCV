from time import time
import cv2
import numpy as np

class Fps():
    def __init__(self, name):
        self.fps_array = np.array([])
        self.average_fps = 0
        self.min_fps = 0
        self.max_fps = 0
        self.fps_array_sort = np.array([])
        self.stats = ""
        self.name = name
        pass
    
    def counter(self,frame, prev_frame_time, name=None, corner = 1):

        if name is None:
            name = "NAN"
        name = name[:4]

        y,x,c = frame.shape
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
        
        text_pos_y = int(pos_y - y*0.03)
        new_frame_time = time()
        fps = 1/(new_frame_time-prev_frame_time)
        fps = int(fps)

        self.fps_array = np.append(self.fps_array, fps)
        self.average_fps = np.mean(self.fps_array)
        self.fps_array_sort = np.sort(self.fps_array)
        if self.fps_array_sort.size > 1: 
            self.min_fps = self.fps_array_sort[1]
        self.max_fps = np.max(self.fps_array)
        self.stats = f"# {self.name} FPS Stats: Average: {self.average_fps:.3f}, Min: {int(self.min_fps)}, Max: {int(self.max_fps)}"

        fps = str(fps)
        frame = cv2.rectangle(frame, rec_start, rec_end, (255,255,255),-1)
        frame = cv2.putText(frame, fps, (pos_x, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        frame = cv2.putText(frame, name + ":", (pos_x, text_pos_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        return frame