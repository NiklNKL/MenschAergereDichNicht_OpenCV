import random

class Game():
    def __init__(self):
        self.current_players = [Player(0), Player(1), Player(2), Player(3)]
        self.finished_players = []

        # Solange die aktive Spielerzahl größer gleich 2 ist, ist das Spiel noch nicht vorbei
        while self.current_players.len() >= 2:
            # Pro Runde werden alle aktiven Spieler durchlaufen
            for p in self.current_players:
                # Falls keine Figur auf dem Spielfeld bewegbar ist, dann 3x Würfeln
                if not p.has_movable_figures():
                    for i in range(0,3):
                        eye_count = self.roll_dice()
                        if eye_count == 6:
                            self.move(p, 6)
                            break
                
                # Normale Würfelrunde, wenn movable Figur vorhanden
                # Falls in einem der drei Würfe eine 6 war, sollte eine movable Figur verfügbar sein
                if p.has_movable_figures():
                    # Solange eine 6 gewürfelt wird und ein move durchgeführt wurde, wird weiter gewürfelt
                    while True:
                        eye_count = self.roll_dice()
                        if not self.move(p, eye_count):
                            break
                        if eye_count != 6:
                            break
                
                # Check whether the current player has finished the game after his move
                if p.check_all_finish():
                    # Add current player to finished players
                    self.finished_players.append(p)
                    # Remove current player from current players
                    self.current_players.remove(p)

                # printe das Feld
                self.print_field()

    def move(self, p_player, p_eye_count):
        print("Available Moves:")
        figures = p_player.get_figures()

        for f in figures:

            # Check ob aus Start raugegangen werden kann
            if f.get_position() == None & p_eye_count == 6:
                print("Figure " + f.get_id() + " (" + f.get_position() + ") yes")
            # Falls Position + Aktuelle Position ist kleiner als 44 und keine Kollision
            elif (f.get_position() + p_eye_count) <= 44 & p_player.is_figure_on_position(f.get_position() + p_eye_count) != True:
                print("Figure " + f.get_id() + " (" + f.get_position() + ") yes")
                # Falls 40 - 44 die neue Position ist, checke ob übersprungene Plätze frei
                
        if p_eye_count == 6 & not p_player.is_figure_on_position():
            

            
        # falls 6 & keiner auf position 0
            # adde figuren vom Start zur Auswahl
        # adde alle figuren ohne collision mit eigenen pieces & aktuelle Position + eye count < 44
        
        # erwarte input welche Figur gemoved werden soll

        # check ob Figur anderer Person dort drauf
            # falls ja: send andere Figur back to start
        # ändere Position eigener Figur



    # initialized field looks like this (player id - home of player id - field - finish of player id):
    # 0 - GGGG - OOOOOOOOOO - OOOO
    # 1 - ÜÜÜÜ - OOOOOOOOOO - OOOO
    # 2 - RRRR - OOOOOOOOOO - OOOO
    # 3 - SSSS - OOOOOOOOOO - OOOO

    def print_field(self):
        print("field")
        

    def roll_dice(self):
        eye_count = random.randrange(1,7)
        return eye_count
    


class Player():
    def __init__(self, p_id):
        self.figures = [Figure(0), Figure(1), Figure(2), Figure(3)]
        self.id = p_id
    
    # Checks whether all figures are located on a start field
    def check_all_start(self):
        for f in self.figures:
            if f.is_start() == False:
                return False
        return True

    # Checks whether all figures are located on a finish field
    def check_all_finish(self):
        for f in self.figures:
            if f.is_finish() == False:
                return False
        return True
    
    # Checks whether there is a figure on a specific position
    def is_figure_on_position(self, p_position):
        for f in self.figures:
            if f.get_position() == p_position:
                return True
        return False
    
    # Checks whether there are movable figures on the field
    def has_movable_figures(self):
        # checke wie viele figuren im start sind
        num_players_start = 0
        for f in self.figures:
            if f.is_start() == True:
                num_players_start + 1

        # Prüfe ob position einer figur kleiner als (44-anzahl startfiguren) ist
        for f in self.figures:
            if f.is_start() == False & f.get_position() < (44-num_players_start):
                return True

        return False
    
    # Return the figures array
    def get_figures(self):
        return self.figures
    
    # Return the id
    def get_id(self):
        return self.id

class Figure():
    def __init__(self, p_id):
        self.position = None
        self.id = p_id
    
    # returns whether the figure is located on a start field
    def is_start(self):
        return self.position == None

    # returns whether the figure is located on a finish field
    def is_finish(self):
        return self.position != None & self.position > 40
    
    # Return the current position
    def get_position(self):
        return self.position
    
    # Return the id
    def get_id(self):
        return self.id

Game()


