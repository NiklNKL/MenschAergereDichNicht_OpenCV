class Field():
	'''Representing a field on the board.

	Objects created from this class will represent a single field
	located on the board.
	'''
	def __init__(self, img_pos:tuple, figure, street_index:int):
		'''Initializes the instance based on the arguments.
		
		Args:
			img_pos: 		x,y,c position on the board in the image
			figure: 		figure object that is located on the field (None if empty)
			street_index:	index of the field on the board from the specified start field
		'''
		self.img_pos = img_pos
		self.figure = figure
		self.street_index = street_index