class Figure():
	def __init__(self, rel_pos:int, player, id:int):
		self.rel_pos = rel_pos
		self.player = player
		self.id = id # 0-3
	
	def get_position(self):
		return self.rel_pos
	
	def set_position(self, p_value):
		self.rel_pos = p_value
	
	# returns whether the figure is located on a start field
	def is_start(self):
		return self.rel_pos == None
	
	# returns whether the figure is located on a finish field
	def is_finish(self):
		is_on_finish = False
		if self.rel_pos != None and self.rel_pos > 39:
				is_on_finish = True
		return is_on_finish
	
	def __str__(self) -> str:
		return f"ID: {self.id}, Relative Position: {self.rel_pos}, Player: {self.player.color}"