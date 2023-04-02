from preparations import Prepare
from handgesture import HandGestureRecognizer
from Dice_Reader import DiceDetector
import cv2
from time import time
import numpy as np


class Logic():
    def __init__(self, diceId, gestureId) -> None:
        self.currentClass = ""
        self.currentDice = 0
        self.turn_number = 0

        if diceId == gestureId:
            cap = cv2.VideoCapture(diceId)
            self.diceHandler = DiceDetector(capId=diceId, cap=cap)
            self.gestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 2, cap=cap)
        else:
            self.diceHandler = DiceDetector(capId=diceId)
            self.gestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 2)

    def choose_move(self, available_moves):
        # return chosen figure object
        pass

    def get_current_dice(self):

        while True:
            newClass = self.gestureHandler.run()
            newDice = self.diceHandler.run()
            print(f"{newClass}  {newDice}")

            if not newClass == self.currentClass and self.currentClass == "thumbs up":
                self.currentClass = newClass 
            elif newClass == "thumbs up" and not self.currentClass == "thumbs up":
                self.currentClass = newClass
                return newDice
            
            ## needed to show video feed constantly
            if cv2.waitKey(1) == ord('q'):
                raise Exception("operation was cancelled")

    def current_gesture(self):
        newClass = self.gestureHandler.run()
        newDice = self.diceHandler.run()
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
    useImg = True

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

    LogicHandler = Logic(diceId = 0, gestureId = 0)

    while True:
        # status = LogicHandler.current_gesture()
        p = BoardgameHandler.players[BoardgameHandler.current_player]
        print(f"It's {p.color}'s turn!")

        ## if no figures are on the street and possible endfield figures are at the end
        if not p.has_movable_figures():
            for _ in range(3):
                try:
                    eye_count = LogicHandler.get_current_dice()
                except Exception:
                    status = 1
                    break

                if eye_count == 6:
                    BoardgameHandler.current_turn(LogicHandler, eye_count)
                    break

        while p.has_movable_figures():
            try:
                eye_count = LogicHandler.get_current_dice()
            except Exception:
                status = 1
                break

            BoardgameHandler.current_turn(LogicHandler, eye_count)
            if eye_count != 6:
                break

        if cv2.waitKey(1) == ord('q') or p.check_all_finish() or status == 1:
            break

        BoardgameHandler.current_player = (BoardgameHandler.current_player + 1) %4

    # release the webcam and destroy all active windows
    cv2.VideoCapture(0).release()
    cv2.destroyAllWindows()