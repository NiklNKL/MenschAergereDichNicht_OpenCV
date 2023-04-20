from enum import Enum

class GameStatus(Enum):
    INITIALIZING = "Game Initialisierungsphase"
    START = "Game kann gestartet werden"
    RUNNING = "Das Game läuft bereits"
    FINISHED = "Das Spiel wurde beendet"
    SHOULD_QUIT = "Soll das Spiel geschlossen werden?"
    QUIT = "Das Spiel wird geschlossen!"

class RoundStatus(Enum):
    PLAYER_GREEN = "Spieler Grün🟢 ist dran"
    PLAYER_RED = "Spieler Rot🔴 ist dran"
    PLAYER_YELLOW = "Spieler Gelb🟡 ist dran"
    PLAYER_BLACK = "Spieler Schwarz⚫ ist dran"
    NO_ROUND = "Keine Runde aktiv"
    
class TurnStatus(Enum):
    NO_TURN = {"text":"Starte das Spiel!", "back": False, "continue": False, "quit": False}
    # PLAYER_READY =  {"text":"Fortfahren und wuerfeln...", "back": False, "continue": True, "quit": True}
    ROLL_DICE =  {"text":"Ui-Text", "back": True, "continue": True, "quit": True}
    ROLL_DICE_HOME =  {"text":"Ui-Text", "back": False, "continue": True, "quit": True}
    SELECT_FIGURE =  {"text":"Du hast X Figuren zur Auswahl. Zeige die Nummer der Figur mit einer Hand an und bestaetige mit einem Daumen hoch!", "back": True, "continue": True, "quit": False}
    SELECT_FIGURE_SKIP =  {"text":"Du hast versagt. Akzeptiere das Ergebnis: ", "back": False, "continue": True, "quit": True}
    SELECT_FIGURE_ACCEPT =  {"text":"Du hast Figur X ausgewaehlt. Fortfahren: | Zurück:", "back": True, "continue": True, "quit": True}
    # MOVE_FIGURE =  {"text":"Bewege Figur X und bestaetige mit:", "back": False, "continue": True, "quit": True}
    KICK =  {"text":"Du hast eine Figur von Player X geschlagen. Weiter so!", "back": False, "continue": False, "quit": False}

