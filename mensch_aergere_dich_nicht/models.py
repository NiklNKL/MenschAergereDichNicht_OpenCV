from mensch_aergere_dich_nicht import Game

class Field():
	def __init__(self, imgPos:tuple, figure, streetIndex:int):
		self.imgPos = imgPos
		self.figure = figure
		self.streetIndex = streetIndex # 0 - 43


class Figure():
	def __init__(self, relPos:int, player, id:int):
		self.relPos = relPos
		self.player = player
		self.id = id # 1-4
	
	def get_position(self):
		return self.relPos
	
	def set_position(self, p_value, coordinates, color, index, UiHandler):
		self.relPos = p_value
		UiHandler.highlighting(coordinates, color, index)
	
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


class Player():
	def __init__(self, color:str, id:int, startField:int, game:Game):
		self.GameHandler = game
		self.color = color
		self.id = id # 0-3
		self.figures = []
		self.startField = startField
		self.finishField = (startField + 39)%40
		self.endfields = None
		self.homefields = None

	def set_homefield(self, homefield):
		self.homefields = [Field(imgPos=(x[1],x[2],x[3]), figure=self.figures[id],streetIndex=None) for id, x in enumerate(homefield)]

	def set_endfield(self, endfield):
		self.endfields = [Field(imgPos=(x[1],x[2],x[3]), figure=None,streetIndex=None) for x in endfield]

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
	
	# Checks whether there are/ is a figure(s) on their start field
	def has_start_figures(self):
		for f in self.figures:
			if f.is_start():
				return True
		return False
	
	def available_moves(self, p_eye_count, UiHandler):
		available_figures = []
		print("Available Moves:")

		# Checks wheather there are figures on their starting position and a figure is located on field 0
		# If yes that figure has to be moved!
		# But this figure could also be blocked by another one of that team's figures
		# That is why we loop through all figures / fields until we find the figure that needs to be / can be moved
		if self.has_start_figures() and self.is_figure_on_position(0):
			pos = 0
			found_free_field = False

			while not found_free_field:
				if self.is_figure_on_position(pos + p_eye_count):
					pos = pos + p_eye_count
				else:
					found_free_field = True

			available_figures.append([self.get_figure_on_position(pos), pos + p_eye_count])

		# Handles the condition when a figure can be moved out of their starting position
		# That is the case when 
		# 1. That team has at least one figure on their starting position
		# 2. There is not a figure from that team located on position 0 (that case should've been handled by the first if)
		# 3. The eye count of the dice is 6
		elif self.has_start_figures() and not self.is_figure_on_position(0) and p_eye_count == 6:
			for f in self.figures:
				if f.is_start():
					available_figures.append([f, 0])

		# If none of the first two cases apply, only a figure that is already on the field can be moved
		else:
			for f in self.figures:
				if not f.is_start():
					new_position = f.get_position() + p_eye_count
					# Checks wheather the new position is smaller than 39 and no collision with their own figures apply
					if (new_position <= 39) & (self.is_figure_on_position(new_position) == False):
						print("Figure " + str(f.id) + " (" + str(f.get_position()) + ") available")
						available_figures.append([f, new_position])

					# Checks wheather the new position is greater than 39 in which case the new position would be located on a finish field
					# Cause we play with the added rule that no figures can be jumped on the finish fields, it needs to be checked if the jumped fields are free
					elif (new_position <= 43) & (self.is_figure_on_position(new_position) == False):
						finish_free = True
						for x in range(40, new_position+1):
							if self.is_figure_on_position(x) == True:
								finish_free = False
								break
						if finish_free:
							print("Figure " + str(f.id) + " (" + str(f.get_position()) + ") available")
							available_figures.append([f, new_position])
			
			#highlighting of all available moves
			if len(available_figures) > 0:
				last_figure = available_figures[-1]
				position = last_figure[1]
				print(position)
				try:
					abs_pos = super().normalize_position(f.player.id, position)
					coordinates = self.GameHandler.fields[abs_pos].imgPos
				except IndexError:
					## remove logic for endfield
					endfieldPos = position % 40
					coordinates = f.player.endfields[endfieldPos].imgPos

				print(coordinates)
				UiHandler.highlighting(coordinates, self.color, self.figures.index)
		
		return available_figures
	
	# Checks whether there is a figure on a specific position
	def is_figure_on_position(self, p_position):
		for f in self.figures:
			if f.get_position() == p_position:
				return True
		return False
	
	# Returns the figure on the desired position
	def get_figure_on_position(self, p_position):
		for f in self.figures:
			if f.get_position() == p_position:
				return f
		return None
	
	# Checks whether all figures are located on a finish field
	def check_all_finish(self):
		for f in self.figures:
			if f.is_finish() == False:
				return 0
		print("You have won!")
		return 1

	def __str__(self) -> str:
		return f"{self.color}"
