import numpy as np
import cv2

class Ui:
    def __init__(self, BoardCap, DiceCap, GestureCap) -> None:
        ## desired size of each frame
        self.shape = (640, 360)

        self.player, self.dice, self.turn, self.prompt, self.movableFigures = "", "", "", "", ""

        ## read frame from cv2.VideoCapture and resize
        self.boardFrame = cv2.resize(BoardCap, self.shape) ## add .read()[1] when using VideCapture instead of image
        self.diceFrame = cv2.resize(DiceCap.read()[1], self.shape)
        self.gestureFrame = cv2.resize(GestureCap.read()[1], self.shape)

        ## create two horizontal stacks
        ## first stacks contains empty frame as background for game status
        overlay = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)
        self.numpy_horizontal_upper = np.hstack((overlay, self.boardFrame))
        self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))
        ## initialize text for game status frame
        self.overlay = self.update_text()
        ## stack the horizontal stacks vertically to get 2x2 format
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))

    def update(self, overlay=None, boardFrame=None, diceFrame=None, gestureFrame=None):
        ## update only frame that was handed over

        ## upper horizontal
        if overlay is not None:
            self.overlay = cv2.resize(overlay, self.shape)
            self.numpy_horizontal_upper = np.hstack((self.overlay, self.boardFrame))
        elif boardFrame is not None:
            self.boardFrame = cv2.resize(boardFrame, self.shape)
            self.numpy_horizontal_upper = np.hstack((self.overlay, self.boardFrame))
        ## lower horizontal
        elif diceFrame is not None:
            self.diceFrame = cv2.resize(diceFrame, self.shape)
            self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))
        elif gestureFrame is not None:
            self.gestureFrame = cv2.resize(gestureFrame, self.shape)
            self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))

        ## stack vertically
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))
        cv2.imshow("Result", self.stream)

    def update_text(self, player=None, turn=None, dice=None, movableFigures=None, prompt=""):
        ## reset current content
        overlay = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)
        
        ## fill with new input
        if player is not None:
            self.player = player
        if turn is not None:
            self.turn = turn
        if dice is not None:
            self.dice = dice
        if movableFigures is not None:
            self.movableFigures = movableFigures

        writeList = [
            f"Player: {self.player}",
            f"Current turn: {self.turn}",
            f"Current dice: {self.dice}",
            f"Movable figures: {movableFigures}",
            f"{prompt}"]
                    
        for index, entry in enumerate(writeList):
            cv2.putText(overlay, 
                    entry,
                    (50,50*(index+1)),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        ## update current game status
        self.update(overlay=overlay)
