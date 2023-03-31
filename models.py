class Boardgame:
	def __init__(self) -> None:
		self.fields = []
		self.figures = []
		self.players = []
		self.current_player = 0
		self.current_attempt = 0

	def current_turn(self, current_dice, figure):
		## get current player
		player = self.players[self.current_player]
		figure = player.figures[figure]
		##ist ein zug möglich

		##falls ja, zug ausführen

		##falls nein





class Field:
	def __init__(self, imgPos:tuple, hasFigure:bool, streetIndex:int):
		self.imgPos = imgPos
		self.hasFigure = hasFigure
		self.streetIndex = streetIndex # 0 - 39

class Figure:
	def __init__(self, relPos:int, player, item:int):
		self.relPos = relPos
		self.player = player
		self.item = item # 1-4

	# returns whether the figure is located on a start field
	def is_start(self):
		return self.relPos == None
	
	def get_position(self):
		return self.relPos
	
	def set_position(self, p_value):
		self.relPos = p_value

	def is_moveable(self, p_eye_count):
		# Check ob aus Start rausgegangen werden kann
		if (self.get_position() == None) & (p_eye_count == 6) & (self.player.is_figure_on_position(0) == False):
			print("Figure " + str(self.get_id()) + " (" + str(self.get_position()) + ") available")
			return True
			#break
		elif (self.get_position() != None):
			# Falls Position + Aktuelle Position kleiner als 44 ist und keine Kollision
			if ((self.get_position() + p_eye_count) <= 39) & (self.player.is_figure_on_position(self.get_position() + p_eye_count) == False):
				print("Figure " + str(self.get_id()) + " (" + str(self.get_position()) + ") available")
				return True
			# Falls 40 - 44 die neue Position ist, checke ob übersprungene Plätze frei
			elif ((self.get_position() + p_eye_count) <= 43) & (self.player.is_figure_on_position(self.get_position() + p_eye_count) == False):
				# Check ob Figuren zwischen letzem normalen Feld und dem Zielfeld im Finish
				finish_free = True
				for x in range(self.get_position()+1, self.get_position() + p_eye_count +1):
					if self.player.is_figure_on_position(x) == True:
						finish_free = False
				if finish_free:
					print("Figure " + str(self.get_id()) + " (" + str(self.get_position()) + ") available")
					return True

class Player:
	def __init__(self, color:str, startField:int):
		self.color = color
		self.figures = []
		self.startField = startField
		self.finishField = (startField + 39)%40
		self.endfields = None

	def set_endfields(self, endfields:list):
		self.endfields = endfields

	# Checks whether there are movable figures on the field
	def has_movable_figures(self):
		# checke wie viele figuren im start sind
		num_players_start = 0
		for f in self.figures:
			if self.is_start() == True:
				num_players_start + 1

		# Prüfe ob position einer figur kleiner als (44-anzahl startfiguren) ist
		for f in self.figures:
			if self.get_position() != None:
				if self.is_start() == False & (int(self.get_position()) < (43-num_players_start)):
					return True

		return False
	
	# Checks whether there is a figure on a specific position
	def is_figure_on_position(self, p_position):
		for f in self.figures:
			if f.get_position() == p_position:
				return True
		return False