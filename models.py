
class Boardgame:
	def __init__(self) -> None:
		self.fields = []
		self.figures = []
		self.players = []
		self.current_player = 0
		self.current_attempt = 0

	def current_turn(self, LogicHandler, eye_count):
		p = self.players[self.current_player]
	
		avail_moves = p.available_moves(eye_count)
		if len(avail_moves) > 0: 
			## Wenn Zug möglich, wähle einen aus
			chosen_figure = LogicHandler.choose_move(avail_moves)
			## führe Zug aus
			self.move(p, chosen_figure, eye_count, LogicHandler.UiHandler)

	def move(self, p_current_player, p_chosen_figure, p_eye_count, UiHandler):
		
		if p_chosen_figure.relPos is not None:
			## remove figure from old field
			old_absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=p_chosen_figure.relPos)
			self.fields[old_absPos].figure = None
		
		##new relative pos
		newPos = self.calculate_new_pos(p_chosen_figure, p_eye_count)
		
		##set field.figure
		try:
			##new abs pos
			absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=newPos)
			
			self.kick(absPos, UiHandler)

			self.fields[absPos].figure = p_chosen_figure
			print(f"NewPos: {newPos}")
			print(f"AbsPos: {absPos}")
		except IndexError:
			## move into endfield
			endfieldPos = newPos % 40
			p_current_player.endfields[endfieldPos].figure = p_chosen_figure

		## set figure.relPos
		print(f"Moved {p_chosen_figure.id} to {newPos}")
		p_chosen_figure.set_position(newPos)

	def calculate_new_pos(self, p_chosen_figure, p_eye_count):
		newPos = 0
		if  p_chosen_figure.relPos is not None:
			newPos = p_chosen_figure.relPos + p_eye_count
		return newPos
		
	def kick(self, absPos, UiHandler):
		if absPos > 39:
			return

		# normalized_new_pos = self.normalize_position(p_current_player.id, p_new_position)
		field = self.fields[absPos]
		
		if field.figure is not None:
			field.figure.set_position(None)
			UiHandler.update_text(prompt=f"figure {field.figure} got kicked!")
			# print(f"figure {field.figure} got kicked!")
		
		# for figure in self.figures:
		# 	try:
		# 		if normalized_new_pos == self.normalize_position(figure.player.id, figure.get_position()):
		# 			figure.set_position = None
		# 			print(f"figure {figure.id} got kicked!")
		# 			break
		# 	except IndexError:
		# 		continue
	
	def normalize_position(self, p_player_id, p_position):
		"""
		normalized = index of field from the perspective of the player 0

		player = 0; pos = 40
		normalized --> 0

		player = 1; pos = 0
		normalized --> 10
		"""
		if p_position is None:
			raise IndexError
		if p_position > 39:
			raise IndexError

		return (p_position + p_player_id * 10) % 40


class Field:
	def __init__(self, imgPos:tuple, figure, streetIndex:int):
		self.imgPos = imgPos
		self.figure = figure
		self.streetIndex = streetIndex # 0 - 43


class Figure:
	def __init__(self, relPos:int, player, id:int):
		self.relPos = relPos
		self.player = player
		self.id = id # 1-4
	
	def get_position(self):
		return self.relPos
	
	def set_position(self, p_value):
		self.relPos = p_value
	
	# returns whether the figure is located on a start field
	def is_start(self):
		return self.relPos == None
	
	# returns whether the figure is located on a finish field
	def is_finish(self):
		is_on_finish = False
		if self.relPos != None and self.relPos > 39:
				is_on_finish = True
		return is_on_finish
	
	def __str__(self) -> str:
		return f"ID: {self.id}, Relative Position: {self.relPos}, Player: {self.player.color}"


class Player:
	def __init__(self, color:str, id:int, startField:int):
		self.color = color
		self.id = id # 0-3
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
			if f.is_start() == True:
				num_players_start + 1

		# Prüfe ob position einer figur kleiner als (43-anzahl Figuren auf dem Feld) ist
		for f in self.figures:
			if f.get_position() != None:
				if f.is_start() == False & (int(f.get_position()) <= (43-(4-num_players_start))):
					return True

		return False
	
	def available_moves(self, p_eye_count):
		available_figures = []
		print("Available Moves:")
		for f in self.figures:
			# Check ob aus Start rausgegangen werden kann
			if (f.is_start()) & (p_eye_count == 6) & (self.is_figure_on_position(0) == False):
				print("Figure " + str(f.id) + " (" + str(f.get_position()) + ") available")
				available_figures.append([f, 0])
				
			elif (not f.is_start()):
				new_position = f.get_position() + p_eye_count
				# Falls Position + Aktuelle Position kleiner als 39 ist und keine Kollision mit eigenen Figuren
				if (new_position <= 39) & (self.is_figure_on_position(new_position) == False):
					print("Figure " + str(f.id) + " (" + str(f.get_position()) + ") available")
					available_figures.append([f, new_position])

				# Falls 39 < newPosition <= 43 die neue Position ist, checke ob übersprungene Plätze frei
				elif (new_position <= 43) & (self.is_figure_on_position(new_position) == False):
					# Check ob Figuren zwischen letzem normalen Feld und dem Zielfeld im Finish
					finish_free = True
					for x in range(40, new_position+1):
						if self.is_figure_on_position(x) == True:
							finish_free = False
							break
					if finish_free:
						print("Figure " + str(f.id) + " (" + str(f.get_position()) + ") available")
						available_figures.append([f, new_position])
		
		return available_figures
	
	# Checks whether there is a figure on a specific position
	def is_figure_on_position(self, p_position):
		for f in self.figures:
			if f.get_position() == p_position:
				return True
		return False
	
	# Checks whether all figures are located on a finish field
	def check_all_finish(self):
		for f in self.figures:
			if f.is_finish() == False:
				return False
		print("You have won!")
		return True
