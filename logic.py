from handgesture import HandGestureRecognizer
from Dice_Reader import DiceDetector
import cv2
from time import time
import numpy as np


class Logic():
    def __init__(self) -> None:
        self.currentClass = ""
        self.currentDice = 0
        self.turn_number = 0

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
    cap = cv2.VideoCapture(1)
    GestureHandler = HandGestureRecognizer(capId = 1, timeThreshold = 3, cap = cap)
    DiceHandler = DiceDetector(capId = 1, cap = cap)
    LogicHandler = Logic()
    while True:
        currentClass = GestureHandler.run()
        currentDice = DiceHandler.run()
        status = LogicHandler.current_turn(currentClass, currentDice)
        if cv2.waitKey(1) == ord('q') or status == 1:
            break
    # release the webcam and destroy all active windows
    cv2.VideoCapture(1).release()
    cv2.destroyAllWindows()