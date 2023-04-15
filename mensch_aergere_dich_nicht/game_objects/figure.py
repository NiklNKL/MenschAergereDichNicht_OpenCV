class Figure():
	def __init__(self, relPos:int, player, id:int):
		self.relPos = relPos
		self.player = player
		self.id = id # 1-4
	
	def get_position(self):
		return self.relPos
	
	def set_position(self, p_value, coordinates, color, index):
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