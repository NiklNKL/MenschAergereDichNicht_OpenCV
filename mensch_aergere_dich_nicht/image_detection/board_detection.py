import cv2
import numpy as np
from mensch_aergere_dich_nicht import game_logic 

class BoardReader():

    def __init__(self, capId, cap = None) -> None:
        # Initialize the webcam 
        if not cap == None:
            self.cap = cap
        else:
            self.cap = cv2.VideoCapture(capId)

    def highlight_moves(self, UIHandler, BoardgameHandler, avail_moves):
        for figure, field in avail_moves:
            # _, board = self.cap.read()
            board = UIHandler.boardFrame
            normPos = game_logic.normalize_position(figure.player, figure.relPos)

            normCord = BoardgameHandler.fields[normPos].imgPos
            newCord = BoardgameHandler.fields[field].imgPos
            
            board = cv2.arrowedLine(board,normCord, newCord,)

