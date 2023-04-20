from .field import Field

class Player():
	'''Representing a player (team) ingame.

	Objects created from this class represent a player (team)
	which has figures, fields and a color etc.	
	'''
	def __init__(self, color:str, id:int, start_field:int):
		'''Initializes the Player

		Args:
			color:			string that describes the player's (team's) color
			id:				id of the player (0-3)
			start_field:	int, relative to the defined start field
		'''
		self.color = color
		self.id = id # 0-3
		self.figures = []
		self.start_field = start_field
		self.finish_field = (start_field + 39)%40
		self.end_fields = None
		self.home_fields = None

	def set_homefield(self, homefield):
		'''Sets the home_fields based on the list provided.'''
		self.home_fields = [Field(img_pos=(x[1],x[2],x[3]), figure=self.figures[id],street_index=None) for id, x in enumerate(homefield)]

	def set_endfield(self, endfield):
		'''Sets the end_fields based on the list provided.'''
		self.end_fields = [Field(img_pos=(x[1],x[2],x[3]), figure=None,street_index=None) for x in endfield]

	def has_movable_figures(self):
		'''Checks whether there are movable figures on the field.
		
		If the figures are either located on finish and/or on the
		home fields then there is no other move possible thatn  
		rolling a 6.
		'''
		# Check how many figures are located on the home fields
		num_players_start = 0
		for f in self.figures:
			if f.is_start() == True:
				num_players_start + 1

		# Check if position of a figure is smaller than 43-count of figures on field
		for f in self.figures:
			if f.get_position() != None:
				if f.is_start() == False & (int(f.get_position()) <= (43-(4-num_players_start))):
					return True

		return False
	
	def has_start_figures(self):
		'''Returns whether there is at least one figure located on its home field'''
		for f in self.figures:
			if f.is_start():
				return True
		return False
	
	def available_figures(self, p_eye_count):
		'''Based on the rolled count, the figures that are available for moving are calculated.
		
		Args:
			p_eye_count: 			int, rolled eye count between 1-6

		Returns:
			available_figures:		array of tuples with figures and their new position
		'''

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
		
		return available_figures
	
	def is_figure_on_position(self, p_position):
		'''Returns whether there is a figure on a specific position
		
		Args:
			p_position:		field position to check for figure on
		'''
		for f in self.figures:
			if f.get_position() == p_position:
				return True
		return False
	
	def get_figure_on_position(self, p_position):
		'''Returns the figure on the desired position. None if no figure on position.
		
		Args:
			p_position:		field position to get the figure from
		'''
		for f in self.figures:
			if f.get_position() == p_position:
				return f
		return None
	
	def all_figures_finished(self):
		'''Returns whether all figures are located on a finish field'''
		for f in self.figures:
			if f.is_finish() == False:
				return False
		print("You have won!")
		return True

	def __str__(self) -> str:
		'''Returns a string of the object.
		
		Override of the __str__() function.
		'''
		return f"{self.color}"
