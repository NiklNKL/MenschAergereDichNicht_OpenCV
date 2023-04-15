import threading
import cv2
from game_objects import Field, Player, Figure

class Game(threading.Thread):
	def __init__(self, DiceThread, HandThread, BoardThread) -> None:

		threading.Thread.__init__(self)

		self.fields = []
		self.figures = []
		self.players = []
		self.current_player = 0

		self.DiceThread = DiceThread
		self.HandThread = HandThread
		self.BoardThread = BoardThread

		self._stop_event = threading.Event()

		self.status = 0

		self.initialized = False

	def create_boardgame(self):
		## create Field objects (streetIndex range [0,39])
		for index, field in enumerate(self.BoardThread.street[self.BoardThread.indexOfGreen:] + self.BoardThread.street[:self.BoardThread.indexOfGreen]):
			self.fields.append(Field(imgPos = field[1:4],
											figure = None,
											streetIndex = index))
		
		## create Player objects
		startField = 0
		for index, color in enumerate(["green", "red", "black", "yellow"]):
			self.players.append(Player(color = color,
												id = index,
												startField = startField
												))
			
			## create Figure objects for each player (id range [1,4])
			for figureNum in range(1,5):
				figure = Figure(relPos = None,
								player = self.players[-1],
								id = figureNum)
				self.figures.append(figure)
				self.players[-1].figures.append(figure)
			startField += 10
		
		## move green's figure 1 to absPos 36 to test endfields
		#self.GameHandler.fields[36].figure = self.GameHandler.players[0].figures[0]
		#self.GameHandler.players[0].figures[0].set_position(36, self.GameHandler.fields[36].imgPos, self.GameHandler.players[0].color, 1, UiHandler)

		## move yellow's figure 1 to absPos 6 to test kick logic
		#self.GameHandler.players[-1].figures[0].set_position(16)
		#self.GameHandler.fields[6].figure = self.GameHandler.players[-1].figures[0]

		## iterate through all players with their respective startfield index
		for index, player in enumerate(self.players):
			homefield = self.BoardThread.homefields[index]
			endfield = self.BoardThread.endfields[index]

			player.set_homefield(homefield)
			player.set_endfield(endfield)

		for figure in self.figures:
			for count in range(0,4):
				pass
				# UiHandler.highlighting(figure.player.homefields[count].imgPos, figure.id, figure.player.color)

		## check if everything was created correctly
		for field in self.fields:
			print({"imgPos": field.imgPos, "figure": field.figure, "streetIndex": field.streetIndex})
		for player in self.players:
			print({"color": player.color, "startField": player.startField, "finishField": player.finishField})
		for figure in self.figures:
			print({"relPos": figure.relPos, "team": figure.player, "item": figure.id})
		print("finished preparations")

	def current_turn(self, eye_count):
		p = self.players[self.current_player]

		avail_moves = p.available_moves(eye_count)
		if len(avail_moves) > 0: 
			## Wenn Zug möglich, wähle einen aus
			chosen_figure = self.choose_figure(avail_moves)
			## führe Zug aus
			self.move(p, chosen_figure, eye_count)

	def move(self, p_current_player, p_chosen_figure, p_eye_count):
		if p_chosen_figure.relPos is not None:
			## remove figure from old field
			try:
				old_absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=p_chosen_figure.relPos)
				self.fields[old_absPos].figure = None
			except IndexError:
				## remove logic for endfield
				endfieldPos = p_chosen_figure.relPos % 40
				p_current_player.endfields[endfieldPos].figure = p_chosen_figure
	
		##new relative pos
		newPos = self.calculate_new_pos(p_chosen_figure, p_eye_count)
	
		##set field.figure
		try:
			##new abs pos
			absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=newPos)
		
			self.kick(absPos)

			field = self.fields[absPos]
			print(f"NewPos: {newPos}")
			print(f"AbsPos: {absPos}")
		except IndexError:
			## move into endfield
			endfieldPos = newPos % 40
			field = p_current_player.endfields[endfieldPos]
		field.figure = p_chosen_figure

		## set figure.relPos
		print(f"Moved {p_chosen_figure.id} to {newPos}")
		p_chosen_figure.set_position(newPos, field.imgPos, p_current_player.color, p_chosen_figure.id)

	def choose_figure(self, available_moves):
		# return chosen figure object
		return available_moves[0][0]

	def get_current_dice(self):
		newDice = 0
		while True and not self.stopped():
			newClass = self.HandThread.currentClass
			
			newDice = self.DiceThread.eye_count
			# print(f"{newClass}  {newDice}")
			# self.BoardHandler.run(self.UiHandler)
			if newDice in range(1,7):
				if newClass == "thumbs up" :
					print(f"retreived {newDice}")
					break
			
			## needed to show video feed constantly
			if cv2.waitKey(1) == ord('q'):
				raise Exception("get_current_dice was cancelled")
			
		return newDice

	def calculate_new_pos(self, p_chosen_figure, p_eye_count):
		newPos = 0
		if  p_chosen_figure.relPos is not None:
			newPos = p_chosen_figure.relPos + p_eye_count
		return newPos
	
	def kick(self, absPos):
		if absPos > 39:
			return
	
		field = self.fields[absPos]
	
		if field.figure is not None:
			field.figure.set_position(None, field.imgPos, field.figure.player.color, field.figure.id)

	def normalize_position(self, p_player_id: int, p_position: int):
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

	def stop(self):
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()
	
	def run(self):

		self.create_boardgame()
		
		self.initialized = True

		while True:
			p = self.players[self.current_player]
			print(f"It's {p}'s turn!")

			## if no figures are on the street and possible endfield figures are at the end
			if not p.has_movable_figures():
				for turn in range(3):
					try:
						eye_count = self.get_current_dice()
					except Exception as e:
						print(e)
						return 1

					if eye_count == 6:
						self.current_turn(eye_count)
						break
			
			while p.has_movable_figures() and not self.stopped():
				try:
					eye_count = self.get_current_dice()
				except Exception as e:
					print(e)
					return 1

				self.current_turn(eye_count)
				if eye_count != 6:
					break
		
			self.status = p.check_all_finish()
			if self.status != 1:
				self.current_player = (self.current_player + 1) %4

			if self.stopped():
				break

		
