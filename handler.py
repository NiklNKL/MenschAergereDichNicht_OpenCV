from mensch_aergere_dich_nicht import Field, Figure, Player, Game
from image_detection import HandGestureRecognizer, DiceDetector, BoardReader
from ui import Ui
import cv2

class Handler():
    def __init__(self, diceId, gestureId, boardId, game: Game) -> None:
        self.currentClass = ""
        self.currentDice = 0
        self.turn_number = 0
        self.GameHandler = game

        if diceId == gestureId == boardId:
            cap = cv2.VideoCapture(diceId)
            self.DiceHandler = DiceDetector(capId=diceId, cap=cap)
            self.GestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 2, cap=cap)
            self.BoardHandler = BoardReader(cap=cap, useImg=True)
        else:
            self.DiceHandler = DiceDetector(capId=diceId)
            self.GestureHandler = HandGestureRecognizer(capId=gestureId, timeThreshold = 2)
            self.BoardHandler = BoardReader(capId=boardId, useImg=True)
        
        self.UiHandler = Ui(self.BoardHandler.frame,
                            self.DiceHandler.frame, 
                            self.GestureHandler.frame)
        
        # initialize game logic and game objects
        street, indexOfGreen, homefields, endfields = self.BoardHandler.prepare()

        self.create_boardgame(UiHandler=self.UiHandler,
                              street=street,
                              start=indexOfGreen,
                              homefields=homefields,
                              endfields=endfields)

    def choose_move(self, available_moves):
        self.UiHandler.update_text(movableFigures = [move[0].id for move in available_moves])
        # return chosen figure object
        return available_moves[0][0]

    def get_current_dice(self):

        while True:
            newClass = self.GestureHandler.run(self.UiHandler)
            newDice = self.DiceHandler.run(self.UiHandler)
            # print(f"{newClass}  {newDice}")
            self.BoardHandler.run(self.UiHandler)
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

        cv2.putText(self.img, str("Turn: " + str(self.currentDice)), (50, 200 ), cv2.FONT_HERSHEY_SIMPLEX, 6, (255, 255, 255), 5)
        cv2.imshow('Current-Turn', self.img)

        return status

    def create_boardgame(self, UiHandler, street, start, homefields, endfields):
        ## create Field objects (streetIndex range [0,39])
        for index, field in enumerate(street[start:] + street[:start]):
            self.GameHandler.fields.append(Field(imgPos = field[1:4],
                                           figure = None,
                                           streetIndex = index))
        
        ## create Player objects
        startField = 0
        for index, color in enumerate(["green", "red", "black", "yellow"]):
            self.GameHandler.players.append(Player(color = color,
                                             id = index,
                                             startField = startField,
                                             game=self.GameHandler))
            
            ## create Figure objects for each player (id range [1,4])
            for figureNum in range(1,5):
                figure = Figure(relPos = None,
                                player = self.GameHandler.players[-1],
                                id = figureNum)
                self.GameHandler.figures.append(figure)
                self.GameHandler.players[-1].figures.append(figure)
            startField += 10
        
        ## move green's figure 1 to absPos 36 to test endfields
        #self.GameHandler.fields[36].figure = self.GameHandler.players[0].figures[0]
        #self.GameHandler.players[0].figures[0].set_position(36, self.GameHandler.fields[36].imgPos, self.GameHandler.players[0].color, 1, UiHandler)

        ## move yellow's figure 1 to absPos 6 to test kick logic
        #self.GameHandler.players[-1].figures[0].set_position(16)
        #self.GameHandler.fields[6].figure = self.GameHandler.players[-1].figures[0]

        ## iterate through all players with their respective startfield index
        for index, player in enumerate(self.GameHandler.players):
            homefield = homefields[index]
            endfield = endfields[index]

            player.set_homefield(homefield)
            player.set_endfield(endfield)

        for figure in self.GameHandler.figures:
            for count in range(0,4):
                UiHandler.highlighting(figure.player.homefields[count].imgPos, figure.id,figure.player.color)

        ## check if everything was created correctly
        for field in self.GameHandler.fields:
            print({"imgPos": field.imgPos, "figure": field.figure, "streetIndex": field.streetIndex})
        for player in self.GameHandler.players:
            print({"color": player.color, "startField": player.startField, "finishField": player.finishField})
        for figure in self.GameHandler.figures:
            print({"relPos": figure.relPos, "team": figure.player, "item": figure.id})
        print("finished preparations")