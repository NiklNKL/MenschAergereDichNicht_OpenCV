class Figure():
	'''Representing a game figure.

	Objects created from this class represent a playable game figure.
	'''
	def __init__(self, rel_pos:int, player, id:int):
		'''Initializes a Figure object.

		Args:
			rel_pos:	position relative to their starting field (0-43)
			player:		player which team the figure is part of
			id:			id in the team (0-3)
		'''
		self.rel_pos = rel_pos
		self.player = player
		self.id = id # 0-3
	
	def get_position(self):
		'''Returns the relative position.'''
		return self.rel_pos
	
	def set_position(self, p_value):
		'''Sets the relative position.'''
		self.rel_pos = p_value
	
	def is_start(self):
		'''Returns whether the figure is located on a start field'''
		return self.rel_pos == None
	
	def is_finish(self):
		'''Returns whether the figure is located on a finish field
		
		Returns True if the relative position of the figure is larger than 39.
		Otherwise it returns False.

		Returns:
			is_on_finish: 	Boolean value if the figure is located on a finish field
		'''
		is_on_finish = False
		if self.rel_pos != None and self.rel_pos > 39:
				is_on_finish = True
		return is_on_finish
	
	def __str__(self) -> str:
		'''Returns a string of the object.
		
		Override of the __str__() function.
		'''
		return f"ID: {self.id}, Relative Position: {self.rel_pos}, Player: {self.player.color}"