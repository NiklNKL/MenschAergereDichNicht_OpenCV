import numpy as np
import cv2
import threading
from time import time
from utilities import Fps
import imutils

class Ui(threading.Thread):
    def __init__(self, dice_thread, hand_thread, board_thread, game_thread, dice_cap, hand_cap, board_cap, use_img = False) -> None:

        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.turn_status = None

        self.player, self.dice, self.turn, self.prompt, self.movable_figures = "", "", "", "", ""
        
        self.game_thread = game_thread
        self.dice_thread = dice_thread
        self.hand_thread = hand_thread
        self.board_thread = board_thread

        self.dice_cap = dice_cap
        self.hand_cap = hand_cap
        self.board_cap = board_cap

        self.board_highlighting_treshold = 0

        self.board_image = cv2.imread('mensch_aergere_dich_nicht/resources/images/test/reallife_frame.jpg', cv2.IMREAD_COLOR)

        self.shape = (1920, 1080)
        self.font_scale_default = self.shape[0]/1920

        self.window_name = "Mensch_aergere_dich_nicht"
        self.frame = np.zeros((self.shape[0], self.shape[1], 3), np.uint8)
        self.board_overlay = np.zeros((self.shape[0], self.shape[1], 3), np.uint8)

        self.dice_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.hand_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.425))
        self.terminal_frame_shape = (int(self.shape[0]*0.4), int(self.shape[1]*0.15))
        self.instruction_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.15))
        self.board_frame_shape = (int(self.shape[0]*0.6), int(self.shape[1]*0.85))

        self.terminal_frame = np.full((self.terminal_frame_shape[1], self.terminal_frame_shape[0], 3), 255, np.uint8)
        self.instruction_frame = np.full((self.instruction_frame_shape[1], self.instruction_frame_shape[0], 3), 255, np.uint8)

        self.use_img = use_img
        
        self.prev_frame_time = 0
        self.fps_tracker = Fps("UI")
        self.stats = ""

    def prepare_frame(self, cap, shape, overlay=None, is_board = False):
        frame = cap.frame
        
        ##crop frame if it is board
        if is_board:
            target = np.float32([[0,0],[self.board_frame_shape[0],0],[0,self.board_frame_shape[1]],[self.board_frame_shape[0],self.board_frame_shape[1]]])
            transform = cv2.getPerspectiveTransform(np.float32(self.game_thread.corners), target)
            
            frame = cv2.warpPerspective(frame, transform, shape)
            
        resize_frame = cv2.resize(frame, shape)

        if overlay is not None:
            if is_board:
                overlay = cv2.warpPerspective(overlay, transform, shape)
            resize_overlay = cv2.resize(overlay, shape)
            ignore_color = np.asarray((0,0,0))
            mask = ~(resize_overlay==ignore_color).all(-1)
            try:
                resize_frame[mask] = cv2.addWeighted(resize_frame[mask], 0, resize_overlay[mask], 1, 0)
            except Exception:
                pass
            final_frame = resize_frame
        else:
            final_frame = resize_frame
        return final_frame
    
    def terminal_text(self, frame, text, x, y):
        return cv2.putText(frame, text ,(x,y), cv2.FONT_HERSHEY_COMPLEX_SMALL, self.font_scale_default*1.2, (0, 0, 0), round(self.font_scale_default*1))

    def update_terminal(self):
        self.terminal_frame = np.full((self.terminal_frame_shape[1], self.terminal_frame_shape[0], 3), 255, np.uint8)
        x,y = self.terminal_frame_shape

        # Appbar
        self.terminal_frame = cv2.rectangle(self.terminal_frame, (0, 0), (x, y), (0,0,0), 3)
        self.terminal_frame = cv2.rectangle(self.terminal_frame, (0, 0), (x, int(0+y*0.25)), (0,0,0), -1)
        self.terminal_frame = cv2.putText(self.terminal_frame, "Terminal" ,(int(0+x*0.4),int(0+y*0.2)), cv2.FONT_HERSHEY_TRIPLEX, self.font_scale_default*1.2, (255, 255, 255), int(self.font_scale_default*1))

        # Info
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.game_status), int(0+x*0.03), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.round_status), int(0+x*0.03), int(0+y*0.7))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.game_thread.turn_status), int(0+x*0.03), int(0+y*0.9))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Finger:", int(0+x*0.8), int(0+y*0.9))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Gesture:", int(0+x*0.54), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, "Dice:", int(0+x*0.8), int(0+y*0.7))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.hand_thread.current_count), int(0+x*0.95), int(0+y*0.9))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.hand_thread.current_gesture), int(0+x*0.71), int(0+y*0.5))
        self.terminal_frame = self.terminal_text(self.terminal_frame, str(self.dice_thread.current_eye_count), int(0+x*0.9), int(0+y*0.7))
        
    def update_instruction(self):
        self.instruction_frame = np.full((self.instruction_frame_shape[1], self.instruction_frame_shape[0], 3), 255, np.uint8)
        x,y = self.instruction_frame_shape
        
        self.instruction_frame = cv2.rectangle(self.instruction_frame, (int(0+x*0.85), y), (x, int(y-y*0.2)), (0,0,0), 2)

        icon_bgra = cv2.imread("mensch_aergere_dich_nicht/resources/images/peace.png", -1)
        icon_bgra = imutils.resize(icon_bgra, height=int(y*0.2))
        alpha_channel = icon_bgra[:,:,-1]
        icon_bgr = icon_bgra[:,:,:-1]
        ROI = self.instruction_frame[y-icon_bgra.shape[0]:y, int(x*0.99)-icon_bgra.shape[1]:int(x*0.99)]
        ROI[alpha_channel==255] = icon_bgr[alpha_channel==255]
        self.instruction_frame[y-icon_bgra.shape[0]:y, int(x*0.99)-icon_bgra.shape[1]:int(x*0.99)] = ROI
        # peace = cv2.resize(peace, ((x-int(0+x*0.85)),int((y*0.2))))
        # self.instruction_frame[y-icon.shape[0]:y, x-icon.shape[1]:x, :]=icon
        # if self.game_thread.turn_status.value.get("continue") == True:
        #     cv2.putText(self.instruction_frame, "Fortfahren:" ,(int(0+x*0.32), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        # if self.game_thread.turn_status.value.get("back") == True:
        #     cv2.putText(self.instruction_frame, "Zurueck:" ,(int(0+x*0.6), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
        if self.game_thread.turn_status.value.get("quit") == True:
            cv2.putText(self.instruction_frame, "Quit game = Peace" ,(int(0+x*0.84), int(0+y*0.93)), cv2.FONT_HERSHEY_PLAIN, self.font_scale_default*1, (0, 0, 0), round(self.font_scale_default*1))
            self.instruction_frame = cv2.rectangle(self.instruction_frame, (int(0+x*0.83), y), (x, int(y-y*0.2)), (0,0,0), 2)

        upper_text = self.get_correct_instruction(upper_text = True)
        lower_text = self.get_correct_instruction(upper_text=False)

        cv2.putText(self.instruction_frame, upper_text ,(int(0+x*0.025),int(0+y*0.5)), cv2.FONT_HERSHEY_PLAIN, self.font_scale_default*2, (0, 0, 0), round(self.font_scale_default*2))
        cv2.putText(self.instruction_frame, lower_text ,(int(0+x*0.025),int(0+y*0.8)), cv2.FONT_HERSHEY_PLAIN, self.font_scale_default*2, (0, 0, 0), round(self.font_scale_default*2))
        
        if str(self.game_thread.round_status.name) == "PLAYER_GREEN":
            color = (35,168,5)
        elif str(self.game_thread.round_status.name) == "PLAYER_RED":
            color = (0,3,204)
        elif str(self.game_thread.round_status.name) == "PLAYER_YELLOW":
            color = (9,180,214)
        elif str(self.game_thread.round_status.name) == "PLAYER_BLACK":
            color = (125,125,125)
        else:
            color = (0,0,0)

        self.instruction_frame = cv2.rectangle(self.instruction_frame, (0, 0), (x, int(0+y*0.25)), color, -1)    
        self.instruction_frame = cv2.rectangle(self.instruction_frame, (0, 0), (x, y), color, 5) 
        self.instruction_frame = cv2.putText(self.instruction_frame, "Game HUB" ,(int(0+x*0.4),int(0+y*0.2)), cv2.FONT_HERSHEY_TRIPLEX, self.font_scale_default*1.2, (255, 255, 255), round(self.font_scale_default*1))

    def figure_ids_to_string(self, figure_array):
        current_figure_id_array = []
        for figure in figure_array:
            current_figure_id_array.append(figure[0].id)
        result = ""
        for index, id in enumerate(current_figure_id_array):
            if len(current_figure_id_array) == 1:
                result = result + str(id+1) + " is "
                
            elif index < len(current_figure_id_array)-1:
                result = result + str(id+1)

                if index + 1 == len(current_figure_id_array)-1:
                    result = result + " and "

                else:
                    result = result + ", "
            else:
                result = result + str(id+1)
        return result

    def get_correct_instruction(self, upper_text):
        game_status = str(self.game_thread.game_status.name)
        turn_status = str(self.game_thread.turn_status.name)
        current_player_color = self.game_thread.players[self.game_thread.current_player].color
        if upper_text:
            if game_status == "SHOULD_QUIT":
                return f"Exit game?"
            elif game_status == "QUIT":
                return f"Ending..."
            elif game_status == "START":
                return f"Game is ready!"
            elif game_status == "FINISHED":
                return f"The game is over!"
            elif turn_status == "ROLL_DICE":
                return f"Player {current_player_color}: Roll the Dice!"
            elif turn_status == "ROLL_DICE_HOME":
                return f"Player {current_player_color}: Roll the Dice! {3-self.game_thread.current_try} tries left ..."
            elif turn_status == "SELECT_FIGURE":
                return f"Figures {self.figure_ids_to_string(self.game_thread.current_turn_available_figures)} are available."
            elif turn_status == "SELECT_FIGURE_ACCEPT":
                return f"Figure {str(self.game_thread.selected_figure.id+1)} was selected."
            elif turn_status == "SELECT_FIGURE_SKIP":
                return f"You used all your tries .."
            elif turn_status == "KICK":
                return f"You kicked a figure! :O"
            else:
                return self.game_thread.turn_status.value.get("text")
        else:
            if game_status == "SHOULD_QUIT":
                return f"Thumbs up to quit"
            elif game_status == "QUIT":
                return f"Have a nice day:)"
            elif game_status == "START":
                return f"Thumbs up to start"
            elif game_status == "FINISHED":
                return f"Player {current_player_color} has won!"
            elif turn_status == "ROLL_DICE":
                return f"You rolled a {self.dice_thread.current_eye_count}"
            elif turn_status == "ROLL_DICE_HOME":
                return f"You rolled a {self.dice_thread.current_eye_count}"
            elif turn_status == "SELECT_FIGURE":
                return f"Show 10 fingers and then the number you want"
            elif turn_status == "SELECT_FIGURE_ACCEPT":
                return f"Accept and move or decline by thumbs up or down"
            elif turn_status == "SELECT_FIGURE_SKIP":
                return f"Next Player get ready ..."
            elif turn_status == "KICK":
                return f"You kicked a figure! :O"
            else:
                return self.game_thread.turn_status.value.get("text")
        
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
            frame = cv2.putText(frame, "Ein Projekt von Jan Schurkemeyer, Mohamed El Bahar, Dominik Ruth, Simon Schruender und Jan Niklas Ewert", (int(0+x*0.005), int(y-y*0.008)), cv2.FONT_HERSHEY_PLAIN, self.font_scale_default*0.8, (0,0,0),round(self.font_scale_default*1))
        else:
            top_bar_width = int(0+y*0.1)
            text_y = int(0+y*0.07)
        frame = cv2.rectangle(frame, (int(0+x*0.3), 0), (int(0+x*0.7), top_bar_width), (0,0,0), -1)    
        frame = cv2.rectangle(frame, (0, 0), (x, y), (0,0,0), 3) 
        frame = cv2.putText(frame, text ,(int(0+x*0.35),text_y), cv2.FONT_HERSHEY_TRIPLEX, self.font_scale_default*1, (255, 255, 255), round(self.font_scale_default*1))
        return frame
    
    def draw_highlighting(self, frame, coordinates, radius, highlighting_color, idx):
        
        #draw circle
        cv2.circle(frame, (int(coordinates[0]), int(coordinates[1])), radius, highlighting_color, round(self.font_scale_default*10))

        #settings for text
        text_font = cv2.FONT_HERSHEY_DUPLEX
        text_scale = self.font_scale_default*1.2
        text_thickness = round(self.font_scale_default*2.5)
        text = str(idx+1)

        text_size, _ = cv2.getTextSize(text, text_font, text_scale, text_thickness)
        text_origin = (int(coordinates[0]) - text_size[0] // 2, int(coordinates[1]) + text_size[1] // 2)

        #add text
        cv2.putText(frame, text, text_origin, text_font, text_scale, (255,255,255), text_thickness, cv2.LINE_AA)

    def highlighting(self):
        
        #create a mask for highlighting
        frame = np.zeros_like(self.board_image, dtype=np.uint8)

        #iterate through figures
        for i, figure in enumerate(self.game_thread.figures):
            coordinates_rel = figure.get_position()
            idx = figure.id
            field_index = None
        
            #get the coordinates of the figure
            try:
                field_index = self.game_thread.normalize_position(figure.player.id, coordinates_rel)
                coordinates = self.game_thread.fields[field_index].img_pos
            except IndexError:
                if coordinates_rel == None:
                    index = i % 4
                    coordinates = figure.player.home_fields[index].img_pos
                else:
                    index = coordinates_rel % 40
                    coordinates = figure.player.end_fields[index].img_pos

            #extract the radius
            radius = int(coordinates[-1])

            coordinates = coordinates[:-1]

            #set highlighting color
            if figure.player.color == "green":
                highlighting_color = (0, 150, 0)
            elif figure.player.color == "red":
                highlighting_color = (0, 0, 255)
            elif figure.player.color == "black":
                highlighting_color = (255, 255, 255)
            else:
                highlighting_color = (0, 215, 255)

            #draw circles with text
            self.draw_highlighting(frame, coordinates, radius, highlighting_color, idx)


        ## move highlighing
        
        #only do move highlighting for certain turn status
        if self.game_thread.turn_status.name == "SELECT_FIGURE" or self.game_thread.turn_status.name == "SELECT_FIGURE_ACCEPT" or self.game_thread.turn_status.name == "MOVE_FIGURE":

            available_figures = self.game_thread.current_turn_available_figures

            #iterate through all availablue figures with their new positions
            for f, new_pos in available_figures:

                #get the coordinates of the new field
                try:
                    field_index = self.game_thread.normalize_position(f.player.id, new_pos)
                    available_figure_coordinates = self.game_thread.fields[field_index].img_pos
                except IndexError:
                    if new_pos == None:
                        index = i % 4
                        available_figure_coordinates = f.player.home_fields[index].img_pos
                    else:
                        index = new_pos % 40
                        available_figure_coordinates = f.player.end_fields[index].img_pos

                #extract the radius of the new field
                available_figure_radius = int(available_figure_coordinates[-1])

                available_figure_coordinates = available_figure_coordinates[:-1]

                #draw highlighting around the potential move field
                self.draw_highlighting(frame, available_figure_coordinates, available_figure_radius, (255, 0, 255), f.id)

        #set turn status to current for performance improvement
        self.turn_status = self.game_thread.turn_status.name
        
        return frame

    def run(self):

        while True:

            if self.turn_status != self.game_thread.turn_status.name:
                self.board_overlay = self.highlighting()

            self.update_instruction()
            self.update_terminal()

            if self.use_img:
                target = np.float32([[0,0],[self.board_frame_shape[0],0],[0,self.board_frame_shape[1]],[self.board_frame_shape[0],self.board_frame_shape[1]]])
                transform = cv2.getPerspectiveTransform(np.float32(self.game_thread.corners), target)
                
                board_frame = cv2.warpPerspective(self.board_image, transform, self.board_frame_shape)
                # board_frame = self.board_image[corner_tl[1]:corner_br[1],corner_tl[0]:corner_br[0],:]
                board_frame = cv2.resize(board_frame, self.board_frame_shape)

                board_overlay_resize = cv2.warpPerspective(self.board_overlay, transform, self.board_frame_shape)
                board_overlay_resize = cv2.resize(board_overlay_resize, self.board_frame_shape)
                board_frame = cv2.bitwise_or(board_overlay_resize, board_frame)

                #bitwise or for testing
            else:
                board_frame = self.prepare_frame(self.board_cap, self.board_frame_shape, self.board_overlay, is_board=True)


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
            self.frame = stream
            self.stats = self.fps_tracker.stats
            
            if self.stopped():  
                break


    
