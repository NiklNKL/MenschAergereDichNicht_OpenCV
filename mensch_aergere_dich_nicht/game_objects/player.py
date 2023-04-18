#from mensch_aergere_dich_nicht import Game
from .field import Field

class Player():
	def __init__(self, color:str, id:int, start_field:int):
		self.color = color
		self.id = id # 0-3
		self.figures = []
		self.start_field = start_field
		self.finish_field = (start_field + 39)%40
		self.end_fields = None
		self.home_fields = None

	def set_homefield(self, homefield):
		self.home_fields = [Field(img_pos=(x[1],x[2],x[3]), figure=self.figures[id],street_index=None) for id, x in enumerate(homefield)]

	def set_endfield(self, endfield):
		self.end_fields = [Field(img_pos=(x[1],x[2],x[3]), figure=None,street_index=None) for x in endfield]

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
	
	def available_figures(self, p_eye_count):
		available_figures = []

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
			
			# #highlighting of all available moves
			# if len(available_figures) > 0:
			# 	last_figure = available_figures[-1]
			# 	position = last_figure[1]
			# 	print(position)
			# 	try:
			# 		abs_pos = super().normalize_position(f.player.id, position)
			# 		coordinates = self.GameHandler.fields[abs_pos].img_pos
			# 	except IndexError:
			# 		## remove logic for endfield
			# 		endfieldPos = position % 40
			# 		coordinates = f.player.end_fields[endfieldPos].img_pos

			# 	print(coordinates)
			# 	UiHandler.highlighting(coordinates, self.figures.index, self.color)
		
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
	def all_figures_finished(self):
		for f in self.figures:
			if f.is_finish() == False:
				return False
		print("You have won!")
		return True

	def __str__(self) -> str:
		return f"{self.color}"
