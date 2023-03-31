from preparations import Prepare
from handgesture import HandGestureRecognizer
from Dice_Reader import DiceDetector
import cv2
from time import time
import numpy as np


class Logic():
    def __init__(self, diceId, gestureId, cap=None) -> None:
        self.currentClass = ""
        self.currentDice = 0
        self.turn_number = 0

        if diceId == gestureId:
            cap = cv2.VideoCapture(diceId)
            self.diceHandler = DiceDetector(capId=diceId, cap=cap)
            self.gestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 3, cap=cap)
        else:
            self.diceHandler = DiceDetector(capId=diceId)
            self.gestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 3)


    def get_current_dice(self):
         
        while True:

            newClass = self.gestureHandler.run()
            newDice = self.diceHandler.run()
            if not newClass == self.currentClass and self.currentClass == "thumbs up":
                self.currentClass = newClass 
            elif newClass == "thumbs up" and not self.currentClass == "thumbs up":
                # self.turn_number += 1
                self.currentDice = newDice
                self.currentClass = newClass
                break
        return newDice

    def current_turn(self, newClass, newDice):
        status = 0
        ## if class change
        if not newClass == self.currentClass and self.currentClass == "thumbs up":
            self.currentClass = newClass 
        elif newClass == "thumbs up" and not self.currentClass == "thumbs up":
            # self.turn_number += 1
            self.currentDice = newDice
            self.currentClass = newClass
            print(self.currentClass)
        elif newClass == "peace" and not self.currentClass == "peace":
            self.currentClass = newClass
            status = 1

        img = np.zeros((400, 800, 3), np.uint8)
        cv2.putText(img, str("Turn: " + str(self.currentDice)), (50, 200 ), cv2.FONT_HERSHEY_SIMPLEX, 6, (255, 255, 255), 5)
        cv2.imshow('Current-Turn', img)

        return status

if __name__ == "__main__":
    useImg = False

    if useImg:
        # frame = cv2.imread('brett.png', cv2.IMREAD_COLOR)
        # frame = cv2.imread('data/empty.JPG', cv2.IMREAD_COLOR)
        frame = cv2.imread('data/wRedAndGreen.JPG', cv2.IMREAD_COLOR)
        # frame = cv2.imread('data/wHand.JPG', cv2.IMREAD_COLOR) # <- case that should not work
        # frame = cv2.imread('data/w2fieldsCovered.jpg', cv2.IMREAD_COLOR) # <- case that should not work
        PrepareHandler = Prepare(frame = frame)
    else:
        capId = 0
        cap = cv2.VideoCapture(capId)
        # PrepareHandler = Prepare(capId = capId)
        PrepareHandler = Prepare(cap = cap)
   
    BoardgameHandler = PrepareHandler.run()

    # GestureHandler = HandGestureRecognizer(capId = 1, timeThreshold = 3, cap = cap)
    # DiceHandler = DiceDetector(capId = 1, cap = cap)
    LogicHandler = Logic(capId = 1, cap = cap)
    while True:
        

        
        
        # currentClass = GestureHandler.run()
        # currentDice = DiceHandler.run()

        # status = LogicHandler.current_turn(currentClass, currentDice)
        if not BoardgameHandler.current_player.has_movable_figures():
            for _ in range(3):
                eye_count = LogicHandler.get_current_dice()
                print(eye_count)
                if eye_count == 6:
                    self.move(p, 6)
                    break
        ## dice übergeben check for possible moves of current player

        ## if possible move
            ## gesture input
        ## repeat move, counter++
        




        if cv2.waitKey(1) == ord('q') or status == 1:
            break
    # release the webcam and destroy all active windows
    cv2.VideoCapture(1).release()
    cv2.destroyAllWindows()