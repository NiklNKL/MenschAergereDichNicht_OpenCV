import numpy as np
import cv2

class Ui:
    def __init__(self, board_frame, dice_frame, gesture_frame) -> None:
        self.shape = (640, 360)

        self.player, self.dice, self.turn, self.prompt, self.movableFigures = "", "", "", "", ""
        
        self.boardFrame = cv2.resize(board_frame, self.shape)
        self.diceFrame = cv2.resize(dice_frame, self.shape)
        self.gestureFrame = cv2.resize(gesture_frame, self.shape)

        self.boardHighlights = np.zeros_like(self.boardFrame, dtype=np.uint8)

        self.numpy_horizontal_upper = np.hstack((np.zeros((self.shape[1], self.shape[0], 3), np.uint8), self.boardFrame))
        self.numpy_horizontal_lower = np.hstack((self.diceFrame, self.gestureFrame))
        self.update_text()
        self.stream = np.vstack((self.numpy_horizontal_upper, self.numpy_horizontal_lower))

    def update(self, overlay=None, boardFrame=None, diceFrame=None, gestureFrame=None):
        ## upper
        if overlay is not None:
            self.overlay = cv2.resize(overlay, self.shape)
            self.numpy_horizontal_upper = np.hstack((self.overlay, self.boardFrame))
        elif boardFrame is not None:
            boardFrame = cv2.resize(boardFrame, self.shape)
            self.boardFrame = cv2.bitwise_or(boardFrame, self.boardHighlights)
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

    def update_text(self, player=None, turn=None, dice=None, movableFigures=None, prompt=""):
        ## reset current content
        self.overlay = np.zeros((self.shape[1], self.shape[0], 3), np.uint8)
        
        ## fill with new input
        if player is not None:
            self.player = player
        if turn is not None:
            self.turn = turn
        if dice is not None:
            self.dice = dice
        if movableFigures is not None:
            self.movableFigures = movableFigures

        cv2.putText(self.overlay, 
                    f"Player: {self.player}",
                    (50,50),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(self.overlay, 
                    f"Current turn: {self.turn}",
                    (50,100),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(self.overlay, 
                    f"Current dice: {self.dice}",
                    (50,150),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        
        cv2.putText(self.overlay, 
                    f"Movable figures: {movableFigures}",
                    (50,200),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        cv2.putText(self.overlay, 
                    f"{prompt}",
                    (50,250),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
            
        self.update(overlay=self.overlay)


    def highlighting(self, coordinates, color, idx, highlithing_color):
        
        #get the original dimensions of the video feed
        #width = int(self.boardFrame.get(cv2.CAP_PROP_FRAME_WIDTH))
        #height = int(self.boardFrame.get(cv2.CAP_PROP_FRAME_HEIGHT)) 

        # height, width, _ = self.boardFrame.shape
        height, width, _ = (4672, 7008, 3) # use this for test with the image

        #transfrom coordinates so they fit to the new frame size
        transformedX = coordinates[0] / width * 640
        transformedY = coordinates[1] / height * 360

        #transfrom the radius
        ratioWidth = width / 640
        ratioHeight = height / 360

        if (ratioWidth == ratioHeight or ratioWidth > ratioHeight):
            transformedRadius = coordinates[2] / ratioWidth
        else:
            transformedRadius = coordinates[2] / ratioHeight
        
        #calculate two points for the rectangle
        pt1 = (int(transformedX - transformedRadius), int(transformedY + transformedRadius))
        pt2 = (int(transformedX + transformedRadius), int(transformedY - transformedRadius))

        #draw a rectangle

        if(highlithing_color == "green"):
            self.boardHighlights = cv2.rectangle(self.boardHighlights, pt1, pt2, (0, 255, 0), 5)
        else: 
            self.boardHighlights = cv2.rectangle(self.boardHighlights, pt1, pt2, (255, 255, 255), 5)
        #Put text with the Figure color and id next to the rectangle
        cv2.putText(self.boardHighlights, f"Figure_{color}_{idx}",pt2, cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 5)
        #cv2.imshow("test", self.boardHighlights)
        #self.update(boardFrame=frame)

    