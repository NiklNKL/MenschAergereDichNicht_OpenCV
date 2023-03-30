class Boardgame:
	def __init__(self) -> None:
		self.fields = []
		self.figures = []
		self.players = []

class Field:
	def __init__(self, imgPos:tuple, hasFigure:bool, streetIndex:int):
		self.imgPos = imgPos
		self.hasFigure = hasFigure
		self.streetIndex = streetIndex # 0 - 39

class Figure:
	def __init__(self, relPos:int, team, item:int):
		self.relPos = relPos
		self.team = team
		self.item = item # 1-4

class Player:
	def __init__(self, color:str, startField:int):
		self.color = color
		self.startField = startField
		self.finishField = (startField + 39)%40
		self.endfields = None

	def set_endfields(self, endfields:list):
		self.endfields = endfields