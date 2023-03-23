import random
import time

class Game():
    def __init__(self):
        self.current_players = [Player(0), Player(1), Player(2), Player(3)]
        self.finished_players = []

        # Solange die aktive Spielerzahl größer gleich 2 ist, ist das Spiel noch nicht vorbei
        while len(self.current_players) >= 2:
            # Pro Runde werden alle aktiven Spieler durchlaufen
            for p in self.current_players:
                print('')
                print("Spieler " + str(p.get_id()) + " ist am Zug.")
                print("Es wird gewürfelt:")

                # Falls keine Figur auf dem Spielfeld bewegbar ist, dann 3x Würfeln
                if not p.has_movable_figures():
                    for i in range(0,3):
                        eye_count = self.roll_dice()
                        print(eye_count)
                        if eye_count == 6:
                            self.move(p, 6)
                            break
                
                # Normale Würfelrunde, wenn movable Figur vorhanden
                # Falls in einem der drei Würfe eine 6 war, sollte eine movable Figur verfügbar sein
                # Solange eine 6 gewürfelt wird und ein move durchgeführt wurde, wird weiter gewürfelt
                while p.has_movable_figures():
                    eye_count = self.roll_dice()
                    print(eye_count)
                    self.move(p, eye_count)
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
        
        print("********* Player " + str(self.finished_players[0].get_id()) + " HAT GEWONNEN *********")

    # Method that gets called when the dice have been rolled
    # Selects the available figures and allows the selection of one of the allowed figures
    # Right now simply the first figure gets selected
    def move(self, p_player, p_eye_count):
        figures = p_player.get_figures()
        available_figures = []

        print("Available Moves:")
        for f in figures:
            # Check ob aus Start rausgegangen werden kann
            if (f.get_position() == None) & (p_eye_count == 6) & (p_player.is_figure_on_position(1) == False):
                print("Figure " + str(f.get_id()) + " (" + str(f.get_position()) + ") available")
                available_figures.append(f)
                #break
            elif (f.get_position() != None):
                # Falls Position + Aktuelle Position kleiner als 44 ist und keine Kollision
                if ((f.get_position() + p_eye_count) <= 40) & (p_player.is_figure_on_position(f.get_position() + p_eye_count) == False):
                    print("Figure " + str(f.get_id()) + " (" + str(f.get_position()) + ") available")
                    available_figures.append(f)
                # Falls 40 - 44 die neue Position ist, checke ob übersprungene Plätze frei
                elif ((f.get_position() + p_eye_count) <= 44) & (p_player.is_figure_on_position(f.get_position() + p_eye_count) == False):
                    # Check ob Figuren zwischen letzem normalen Feld und dem Zielfeld im Finish
                    finish_free = True
                    for x in range(f.get_position()+1, f.get_position() + p_eye_count +1):
                        if p_player.is_figure_on_position(x) == True:
                            finish_free = False
                    if finish_free:
                        print("Figure " + str(f.get_id()) + " (" + str(f.get_position()) + ") available")
                        available_figures.append(f)

        # Falls mindestens eine Figur verfügbar --> checke ob gegnerische Figur bereits auf Feld und ändere die Positionen accordingly
        if len(available_figures) == 0:
            print("Skip cause no figure can be moved!")
        else:
            if available_figures[0].get_position() == None:

                #Check ob Figur anderer Person bereits auf dem Feld
                f_normalized_position = (((p_player.get_id() *10) + 1)) % 40
                for p2 in self.current_players:
                    for f2 in p2.get_figures():
                        if (f2.get_position() != None) & (p2.get_id() != p_player.get_id()):
                            f2_normalized_position = (((p2.get_id() *10) + f2.get_position())) % 40
                            if f_normalized_position == f2_normalized_position:
                                f2.set_position(None)
                                print("Spieler rausgeworfen!!!!!!!!!!!!!!!!!!!")

                available_figures[0].set_position(1)

            elif (available_figures[0].get_position() <=44):
                
                #Check ob Figur anderer Person bereits auf dem Feld
                f_normalized_position = (((p_player.get_id() *10) + available_figures[0].get_id() + p_eye_count)) % 40
                for p2 in self.current_players:
                    for f2 in p2.get_figures():
                        if (f2.get_position() != None) & (p2.get_id() != p_player.get_id()):
                            f2_normalized_position = (( (p2.get_id() *10) + f2.get_position())) % 40
                            if f_normalized_position == f2_normalized_position:
                                f2.set_position(None)
                                print("Spieler rausgeworfen!!!!!!!!!!!!!!!!!!!")

                available_figures[0].set_position(available_figures[0].get_position() + p_eye_count)

    # Method that prints the field in the console
    # Initialized field looks like this:
    # Red = 0; 
    # Field:
    # OOOOOOOOOO OOOOOOOOOO OOOOOOOOOO OOOOOOOOOO
    # 0 - 0123 - OOOO 
    # 1 - 0123 - OOOO 
    # 2 - 0123 - OOOO
    # 3 - 0123 - OOOO

    def print_field(self):
        field = ['O']*40
        for p in self.current_players:
            for f in p.get_figures():
                if (f.get_position() != None):
                    if (f.get_position() <= 40):
                        #print(str((40 - ( (p.get_id() *10) + f.get_position())) % 40))
                        field[((( (p.get_id() *10) + f.get_position())) % 40)-1] = p.get_id()
        
        print("Field:")
        print(field)
        
        for p in self.current_players:
            start = ['O']*4
            finish = ['O']*4
            for f in p.get_figures():
                if f.get_position() == None:
                    start[f.get_id()] = f.get_id()
                elif f.get_position() > 40:
                    finish[(f.get_position() % 40)-1] = f.get_id()
            
            print(start)
            print(finish)
        #time.sleep(0.5)

    # Method that returns an int from 1 to 6
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
            if f.get_position() != None:
                if f.is_start() == False & (int(f.get_position()) < (44-num_players_start)):
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
        is_on_finish = False
        if self.position != None:
            if self.position > 40:
                is_on_finish = True
        return is_on_finish
    
    # Return the current position
    def get_position(self):
        return self.position
    
    def set_position(self, p_value):
        self.position = p_value
    
    # Return the id
    def get_id(self):
        return self.id

Game()


