import numpy as np
import cv2

class Ui:
    def __init__(self, BoardCap, DiceCap, GestureCap) -> None:
        self.shape = (640, 360)

        self.player, self.dice, self.turn, self.prompt, self.movableFigures = "", "", "", "", ""
        
        self.boardFrame = cv2.resize(BoardCap, self.shape) # read when using VideCapture
        self.diceFrame = cv2.resize(DiceCap.read()[1], self.shape)
        self.gestureFrame = cv2.resize(GestureCap.read()[1], self.shape)

        self.numpy_horizontal_upper = np.hstack((np.zeros((self.shape[1], self.shape[0], 3), np.uint8), self.boardFrame))
        self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))
        self.overlay = self.update_text()
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))

    def update(self, overlay=None, boardFrame=None, diceFrame=None, gestureFrame=None):
        ## upper
        if overlay is not None:
            self.overlay = cv2.resize(overlay, self.shape)
            self.numpy_horizontal_upper = np.hstack((self.overlay, self.boardFrame))
        elif boardFrame is not None:
            self.boardFrame = cv2.resize(boardFrame, self.shape)
            self.numpy_horizontal_upper = np.hstack((self.overlay, self.boardFrame))
        ## lower
        elif diceFrame is not None:
            self.diceFrame = cv2.resize(diceFrame, self.shape)
            self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))
        elif gestureFrame is not None:
            self.gestureFrame = cv2.resize(gestureFrame, self.shape)
            self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))

        ## stack
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))
        cv2.imshow("Result", self.stream)

    def update_text(self, player=None, turn=None, dice=None, movableFigures=None, prompt=None):
        ## reset current content
        overlay = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)
        
        ## fill with new input
        if player is not None:
            self.player = player
        if turn is not None:
            self.turn = turn
        if dice is not None:
            self.dice = dice
        if prompt is not None:
            self.prompt = prompt
        if movableFigures is not None:
            self.movableFigures = movableFigures

        cv2.putText(overlay, 
                    f"Player: {self.player}",
                    (50,50),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(overlay, 
                    f"Current turn: {self.turn}",
                    (50,100),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(overlay, 
                    f"Current dice: {self.dice}",
                    (50,150),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(overlay, 
                    f"Movable figures: {movableFigures}",
                    (50,200),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(overlay, 
                    f"{self.prompt}",
                    (50,250),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
            
        self.update(overlay=overlay)
