from preparations import Prepare
from image_detection import HandGestureRecognizer, DiceDetector
from ui import Ui
import cv2

class Handler():
    def __init__(self, diceId, gestureId, boardId, boardFrame=None) -> None:
        self.currentClass = ""
        self.currentDice = 0
        self.turn_number = 0
        
        ## initialize modules in image_detection packet and the Prepare class
        ## if all deviceIds for the camera to be used are the same, create a VideCapture object
        if diceId == gestureId == boardId:
            cap = cv2.VideoCapture(diceId)
            self.DiceHandler = DiceDetector(capId=diceId, cap=cap)
            self.GestureHandler = HandGestureRecognizer(capId=gestureId,
                                                        timeThreshold = 2,
                                                        cap=cap)
            ## decide wether image is used for tests of Prepare 
            if boardFrame is None:
                self.PrepareHandler = Prepare(capId=boardId, cap=cap)
            else:
                self.PrepareHandler = Prepare(capId=boardId, frame=boardFrame)
        else:
            self.DiceHandler = DiceDetector(capId=diceId)
            self.GestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 2)
            ## decide wether image is used for tests of Prepare 
            if boardFrame is None:
                self.PrepareHandler = Prepare(capId=boardId)
            else:
                self.PrepareHandler = Prepare(capId=boardId, frame=boardFrame)
        
        ## initialize the UI with all cv2.VideCapture objects
        self.UIHandler = Ui(self.PrepareHandler.frame, #self.PrepareHandler.cap
                            self.DiceHandler.cap, 
                            self.GestureHandler.cap) 
        
        ## excecute preparations to create objects for the game_logic
        self.PrepareHandler.run() 

    def choose_move(self, available_moves):
        self.UIHandler.update_text(movableFigures = [move[0].id for move in available_moves])
        # return chosen figure object
        return available_moves[0][0]

    def get_current_dice(self):

        while True:
            newClass = self.GestureHandler.run(self.UIHandler)
            newDice = self.DiceHandler.run(self.UIHandler)
            # print(f"{newClass}  {newDice}")
            if newDice in range(1,7):
                if not newClass == self.currentClass and self.currentClass == "thumbs up":
                    self.currentClass = newClass 
                elif newClass == "thumbs up" and not self.currentClass == "thumbs up":
                    self.currentClass = newClass
                    print(f"retreived {newDice}")
                    break
            
            ## needed to show video feed constantly
            if cv2.waitKey(1) == ord('q'):
                raise Exception("get_current_dice was cancelled")
            
        return newDice

    def current_gesture(self):
        newClass = self.GestureHandler.run()
        newDice = self.DiceHandler.run()
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

        cv2.putText(self.img, str("Turn: " + str(self.currentDice)), (50, 200 ),
                     cv2.FONT_HERSHEY_SIMPLEX, 6, (255, 255, 255), 5)
        cv2.imshow('Current-Turn', self.img)

        return status