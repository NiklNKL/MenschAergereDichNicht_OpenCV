import numpy as np
import cv2
import threading
from time import time
from utilities import Fps

class Ui(threading.Thread):
    def __init__(self, dice_thread, hand_thread, board_thread, game_thread, dice_cap, hand_cap, board_cap, use_img = False) -> None:

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

        self.board_image = cv2.imread('mensch_aergere_dich_nicht/resources/images/test/wRedAndGreen.JPG', cv2.IMREAD_COLOR)

        self.shape = (1920, 1080)

        self.window_name = "Mensch_aergere_dich_nicht"

        self.dice_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.hand_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.terminal_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.15))
        self.instruction_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.15))
        self.board_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.85))

        self.terminal_frame = np.full((self.terminal_frame_shape[1], self.terminal_frame_shape[0], 3), 255, np.uint8)
        self.instruction_frame = np.full((self.instruction_frame_shape[1], self.instruction_frame_shape[0], 3), 255, np.uint8)

        self.use_img = use_img
        self.exit = False
        

        self.prev_frame_time = 0
        self.fps_tracker = Fps("UI")
        self.stats = ""

    def prepare_frame(self, cap, shape, overlay=None):
        frame = cap.frame
        resize_frame = cv2.resize(frame, shape)
        if overlay is not None:
            resize_overlay = cv2.resize(overlay, shape)
            final_frame = cv2.bitwise_or(resize_overlay, resize_frame)
        else:
            final_frame = resize_frame
        return final_frame
    
    def terminal_text(self, frame, text, x, y):
        return cv2.putText(frame, text ,(x,y), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.2, (0, 0, 0), 1)

    def update_terminal(self):
        self.terminal_frame = np.full((self.terminal_frame_shape[1], self.terminal_frame_shape[0], 3), 255, np.uint8)
        x,y = self.terminal_frame_shape

        # Appbar
        self.terminal_frame = cv2.rectangle(self.terminal_frame, (0, 0), (x, y), (0,0,0), 3)
        self.terminal_frame = cv2.rectangle(self.terminal_frame, (0, 0), (x, int(0+y*0.25)), (0,0,0), -1)
        self.terminal_frame = cv2.putText(self.terminal_frame, "Terminal" ,(int(0+x*0.4),int(0+y*0.2)), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255, 255, 255), 1)

        # Info
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.game_status), int(0+x*0.03), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.round_status), int(0+x*0.03), int(0+y*0.7))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.turn_status), int(0+x*0.03), int(0+y*0.9))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Finger:", int(0+x*0.63), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Gesture:", int(0+x*0.63), int(0+y*0.7))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Dice:", int(0+x*0.63), int(0+y*0.9))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.hand_thread.currentCount), int(0+x*0.80), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.hand_thread.currentClass), int(0+x*0.80), int(0+y*0.7))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.dice_thread.eye_count), int(0+x*0.80), int(0+y*0.9))
        
    def update_instruction(self):
        self.instruction_frame = np.full((self.instruction_frame_shape[1], self.instruction_frame_shape[0], 3), 255, np.uint8)
        x,y = self.instruction_frame_shape
        
        self.instruction_frame = cv2.rectangle(self.instruction_frame, (int(0+x*0.3), y), (int(0+x*0.7), int(y-y*0.2)), (0,0,0), 2)
        if self.game_thread.turn_status.value.get("continue") == True:
            cv2.putText(self.instruction_frame, "Fortfahren:" ,(int(0+x*0.32), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        if self.game_thread.turn_status.value.get("back") == True:
            cv2.putText(self.instruction_frame, "Zurueck:" ,(int(0+x*0.6), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        if self.game_thread.turn_status.value.get("quit") == True:
            cv2.putText(self.instruction_frame, "Spiel beenden:" ,(int(0+x*0.45), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            

        text = self.get_correct_instruction()
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_PLAIN, 3, 2)[0]
        text_x = int((self.instruction_frame.shape[1] - text_size[0]) / 2)
        text_y = int((self.instruction_frame.shape[0] + text_size[1]) / 2)

        cv2.putText(self.instruction_frame, text ,(text_x,text_y), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 2)
        
        if str(self.game_thread.round_status.name) == "PLAYER_GREEN":
            color = (5,168,35)
        elif str(self.game_thread.round_status.name) == "PLAYER_RED":
            color = (204,3,0)
        elif str(self.game_thread.round_status.name) == "PLAYER_YELLOW":
            color = (214,180,9)
        elif str(self.game_thread.round_status.name) == "PLAYER_BLACK":
            color = (125,125,125)
        else:
            color = (0,0,0)

        self.instruction_frame = cv2.rectangle(self.instruction_frame, (0, 0), (x, int(0+y*0.25)), color, -1)    
        self.instruction_frame = cv2.rectangle(self.instruction_frame, (0, 0), (x, y), color, 5) 
        self.instruction_frame = cv2.putText(self.instruction_frame, "Game HUB" ,(int(0+x*0.4),int(0+y*0.2)), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (255, 255, 255), 1)

    def get_correct_instruction(self):
        if str(self.game_thread.turn_status.name) == "ROLL_DICE":
            return f"Du hast eine {self.dice_thread.eye_count} gewuerfelt."
        elif str(self.game_thread.turn_status.name) == "SELECT_FIGURE":
            return f"Du hast {self.game_thread.current_figure_ids} Figuren zur Auswahl."
        elif str(self.game_thread.turn_status.name) == "SELECT_FIGURE_ACCEPT":
            return f"Du hast Figur {self.game_thread.selected_figure} gewaehlt."
        elif str(self.game_thread.turn_status.name) == "KICK":
            return f"Du hast eine Figur von Spieler X geschlagen"
        else:
            return self.game_thread.turn_status.value.get("text")
        # if str(self.game_thread.game_status) == "GameStatus.RUNNING":
        #     
        # else:
        #     return self.game_thread.game_status.value
        
    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def draw_frame(self, frame, text, is_board = False):
        y,x,c = frame.shape
        if is_board:
            top_bar_width = int(0+y*0.055)
            text_y = int(0+y*0.038)
            frame = cv2.rectangle(frame, (0, int(y-y*0.025)), (int(0+x*0.65), y), (0,0,0), 2)
            frame = cv2.rectangle(frame, (0, int(y-y*0.025)), (int(0+x*0.65), y), (255,255,255), -1)
            frame = cv2.putText(frame, "Ein Projekt von Jan Schurkemeyer, Mohamed El Bahar, Dominik Ruth, Simon Schruender und Jan Niklas Ewert", (int(0+x*0.005), int(y-y*0.008)), cv2.FONT_HERSHEY_PLAIN, 0.8, (0,0,0),1)
        else:
            top_bar_width = int(0+y*0.1)
            text_y = int(0+y*0.07)
        frame = cv2.rectangle(frame, (int(0+x*0.3), 0), (int(0+x*0.7), top_bar_width), (0,0,0), -1)    
        frame = cv2.rectangle(frame, (0, 0), (x, y), (0,0,0), 3) 
        frame = cv2.putText(frame, text ,(int(0+x*0.35),text_y), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 255, 255), 1)
        return frame

    def run(self):
        while True:
            self.update_instruction()
            self.update_terminal()
            if self.use_img:
                board_frame = cv2.resize(self.board_image, self.board_frame_shape)
            else:
                board_frame = self.prepare_frame(self.board_cap, self.board_frame_shape)

            dice_frame = self.prepare_frame(self.dice_cap, self.dice_frame_shape, self.dice_thread.overlay)

            hand_frame = self.prepare_frame(self.hand_cap, self.hand_frame_shape, self.hand_thread.overlay)

            board_frame = self.draw_frame(board_frame, "Boardgame-Camera", is_board=True)
            dice_frame = self.draw_frame(dice_frame, "Dice-Camera")
            hand_frame = self.draw_frame(hand_frame, "Hand-Camera")

            numpy_horizontal_upper = np.hstack((self.terminal_frame, self.instruction_frame))
            left_vertical = np.vstack((dice_frame, hand_frame))

            ## lower

            numpy_horizontal_lower = np.hstack((left_vertical, board_frame))

            ## stack vertically
            stream = np.vstack((numpy_horizontal_upper, numpy_horizontal_lower))
            stream = self.fps_tracker.counter(stream, self.prev_frame_time, name="UI", corner=4)
            self.prev_frame_time = time()
            cv2.imshow(self.window_name, stream)

            key = cv2.waitKey(20)
            if key == 27:  # exit on ESC
                self.exit = True
                self.stats = self.fps_tracker.stats
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
