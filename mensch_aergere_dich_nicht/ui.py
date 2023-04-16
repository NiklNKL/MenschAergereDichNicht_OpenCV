import numpy as np
import cv2
import threading
from time import time

class Ui(threading.Thread):
    def __init__(self, dice_thread, hand_thread, board_thread, game_thread, dice_cap, hand_cap, board_cap) -> None:

        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.player, self.dice, self.turn, self.prompt, self.movable_figures = "", "", "", "", ""
        
        self.game_thread = game_thread
        self.dice_thread = dice_thread
        self.hand_thread = hand_thread
        self.board_thread = board_thread

        self.dice_cap = dice_cap
        self.hand_cap = hand_cap
        self.board_cap = board_cap

        self.shape = (1920, 1080)

        self.window_name = "Mensch_aergere_dich_nicht"

        self.dice_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.hand_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.terminal_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.15))
        self.instruction_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.15))
        self.board_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.85))

        self.terminal_frame = np.zeros((self.terminal_frame_shape[1], self.terminal_frame_shape[0], 3), np.uint8)
        self.instruction_frame = np.full((self.instruction_frame_shape[1], self.instruction_frame_shape[0], 3),255, np.uint8)

        self.exit = False

        self.prev_frame_time = 0
        self.new_frame_time = 0

    def prepare_frame(self, cap, shape, overlay=None ):
        frame = cap.frame
        resize_frame = cv2.resize(frame, shape)
        if overlay is not None:
            resize_overlay = cv2.resize(overlay, shape)
            merged_frame = cv2.bitwise_or(resize_overlay, resize_frame)
            return merged_frame
        return resize_frame


    def update_text(self, player=None, turn=None, dice=None, movable_figures=None, prompt=""):
        ## reset current content
        self.overlay = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)
        
        ## fill with new input
        if player is not None:
            self.player = player
        if turn is not None:
            self.turn = turn
        if dice is not None:
            self.dice = dice
        if movable_figures is not None:
            self.movable_figures = movable_figures

        cv2.putText(self.info_frame, 
                    f"Player: {self.player}",
                    (50,50),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(self.info_frame, 
                    f"Current turn: {self.turn}",
                    (50,100),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(self.info_frame, 
                    f"Current dice: {self.dice}",
                    (50,150),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(self.info_frame, 
                    f"Movable figures: {movable_figures}",
                    (50,200),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(self.info_frame, 
                    f"{prompt}",
                    (50,250),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
            
        self.update()
    
    def fps(self, frame):
        self.new_frame_time = time()
        fps = 1/(self.new_frame_time-self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time
        fps = int(fps)
        fps = str(fps)
        return cv2.putText(frame, fps, (1790, 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 3, cv2.LINE_AA)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            
            board_frame = self.prepare_frame(self.board_cap, self.board_frame_shape)
            dice_frame = self.prepare_frame(self.dice_cap, self.dice_frame_shape)
            hand_frame = self.prepare_frame(self.hand_cap, self.hand_frame_shape)
        
            numpy_horizontal_upper = np.hstack((self.terminal_frame, self.instruction_frame))
            left_vertical = np.vstack((dice_frame, hand_frame))

            ## lower

            numpy_horizontal_lower = np.hstack((left_vertical, board_frame))

            ## stack vertically
            stream = np.vstack((numpy_horizontal_upper, numpy_horizontal_lower))
            stream = self.fps(stream)
            cv2.imshow(self.window_name, stream)

            key = cv2.waitKey(20)
            if key == 27:  # exit on ESC
                self.exit = True
                cv2.destroyAllWindows()
                break
            if self.stopped():
                break


    # def highlighting(self, coordinates, idx, highlighting_color):
        
    #     #get the original dimensions of the video feed
    #     #width = int(self.boardFrame.get(cv2.CAP_PROP_FRAME_WIDTH))
    #     #height = int(self.boardFrame.get(cv2.CAP_PROP_FRAME_HEIGHT)) 

    #     # height, width, _ = self.boardFrame.shape
    #     height, width, _ = (4672, 7008, 3) # use this for test with the image

    #     #transfrom coordinates so they fit to the new frame size
    #     transformedX = coordinates[0] / width * 640
    #     transformedY = coordinates[1] / height * 360

    #     #transfrom the radius
    #     ratioWidth = width / 640
    #     ratioHeight = height / 360

    #     if (ratioWidth == ratioHeight or ratioWidth > ratioHeight):
    #         transformedRadius = coordinates[2] / ratioWidth
    #     else:
    #         transformedRadius = coordinates[2] / ratioHeight
        
    #     #calculate two points for the rectangle
    #     # center = [transformedX, transformedY]

    #     #draw a circle
    #     # cv2.circle(self.boardHighlights, center, transformedRadius, highlighting_color, 5)
        
    #     #Id in den Kreis schreiben
    #     font = cv2.FONT_HERSHEY_SIMPLEX
    #     text = idx
    #     text_size, _ = cv2.getTextSize(text, font, 1, 2)
    #     text_x = int(100 - text_size[0]/2)
    #     text_y = int(100 + text_size[1]/2)
    #     cv2.putText(self.boardHighlights, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    #     #Put text with the Figure color and id next to the rectangle
    #     #cv2.putText(self.boardHighlights, f"Figure_{color}_{idx}",pt2, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 5)
    #     #cv2.imshow("test", self.boardHighlights)
    #     #self.update(boardFrame=frame)
