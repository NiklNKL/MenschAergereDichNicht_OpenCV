import numpy as np
import cv2
import threading
import time

class Ui(threading.Thread):
    def __init__(self, dice_thread, hand_thread, board_thread, game_thread, dice_cap, hand_cap, board_cap) -> None:

        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.shape = (640, 360)
        # self.cap = cap
        # _, self.frame = self.cap.read()
        self.player, self.dice, self.turn, self.prompt, self.movable_figures = "", "", "", "", ""
        
        self.game_thread = game_thread
        self.dice_thread = dice_thread
        self.hand_thread = hand_thread
        self.board_thread = board_thread

        self.dice_cap = dice_cap
        self.hand_cap = hand_cap
        self.board_cap = board_cap

        # self.board_frame = self.board_thread.frame
        # self.dice_overlay = self.dice_thread.overlay
        # self.hand_frame = self.hand_thread.frame

        self.info_frame = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)

        self.exit = False

        # self.board_frame = cv2.resize(self.board_thread.frame, self.shape)
        # self.dice_frame = cv2.resize(self.dice_thread.frame, self.shape)
        # self.hand_frame = cv2.resize(self.hand_thread.frame, self.shape)
        # self.info_frame = cv2.resize(self.info_frame, self.shape)

        # self.board_highlights = np.zeros_like(self.board_frame, dtype=np.uint8)

        # ## create two horizontal stacks
        # ## first stacks contains empty frame as background for game status
        
        # self.numpy_horizontal_upper = np.hstack((self.info_frame, self.board_frame))
        # self.numpy_horizontal_lower = np.hstack((self.dice_frame, self.hand_frame))
        # self.update_text()
        # self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))


    def prepare_frame(self, cap, shape, overlay=None ):
        frame = cap.frame
        resize_frame = cv2.resize(frame, shape)
        if overlay is not None:
            resize_overlay = cv2.resize(overlay, shape)
            merged_frame = cv2.bitwise_or(resize_overlay, resize_frame)
            return merged_frame
        return resize_frame

    def update(self):

        # self.board_frame = cv2.resize(self.board_thread.frame, self.shape)
        # self.dice_frame = cv2.resize(self.dice_thread.frame, self.shape)
        # self.hand_frame = cv2.resize(self.hand_thread.frame, self.shape)
        info_frame = cv2.resize(self.info_frame, self.shape)

        board_frame = self.prepare_frame(self.board_cap, self.shape)
        dice_frame = self.prepare_frame(self.dice_cap, self.shape, self.dice_thread.overlay)
        hand_frame = self.prepare_frame(self.hand_cap, self.shape, self.hand_thread.overlay)

        ## update only frame that was handed over

        ## upper horizontal
        
        # self.board_frame = cv2.bitwise_or(self.board_frame, self.board_highlights)
        self.numpy_horizontal_upper = np.hstack((info_frame, board_frame))

        ## lower

        self.numpy_horizontal_lower = np.hstack((dice_frame, hand_frame))

        ## stack vertically
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))
        cv2.imshow("Mensch_aergere_dich_nicht", self.stream)

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
    
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            # t = 1/60
            # time.sleep(t)
            self.update()
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