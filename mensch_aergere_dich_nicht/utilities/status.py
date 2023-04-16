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
    NO_TURN = "Kein Zug aktiv"
    PLAYER_READY = "Daumen hoch 👍, wenn du bereit bist und würfle🎲 anschließend!"
    ROLL_DICE = "Du hast eine X gewürfelt. Fortfahren: 👍 | Zurück: 👎"
    SELECT_FIGURE = "Du hast X Figuren zur Auswahl. Zeige die Nummer der Figur mit einer Hand ✋ an und bestätige mit einem Daumen hoch!"
    SELECT_FIGURE_SKIP = "Du hast versagt. Akzeptiere das Ergebnis: "
    SELECT_FIGURE_ACCEPT = "Du hast Figur X ausgewählt. Fortfahren: 👍 | Zurück: 👎"
    MOVE_FIGURE = "Bewege Figur X und bestätige mit: 👍"
    KICK = "Du hast eine Figur von Player X geschlagen. Weiter so!"

