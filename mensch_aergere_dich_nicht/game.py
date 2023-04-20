import threading
import cv2
from game_objects import Field, Player, Figure
from utilities import GameStatus, RoundStatus, TurnStatus
import time

class Game(threading.Thread):
	def __init__(self, dice_thread, hand_thread, board_thread) -> None:

		threading.Thread.__init__(self)

		self.corners = []
		
		self.fields = []
		self.figures = []
		self.players = []
		self.current_player = 0

		self.selected_figure = 0
		self.current_turn_eye_count = 0
		self.current_turn_available_figures = []
		self.current_try = 0

		self.dice_thread = dice_thread
		self.hand_thread = hand_thread
		self.board_thread = board_thread

		self._stop_event = threading.Event()

		self.status = 0

		self.game_status = GameStatus.INITIALIZING
		self.round_status = RoundStatus.NO_ROUND
		self.turn_status = TurnStatus.NO_TURN

		self.initialized = False

	def create_boardgame(self):
		## create Field objects (street_index range [0,39])
		for index, field in enumerate(self.board_thread.street[self.board_thread.index_of_green:] + self.board_thread.street[:self.board_thread.index_of_green]):
			self.fields.append(Field(img_pos = field[1:4],
											figure = None,
											street_index = index))
		
		## create Player objects
		start_field = 0
		for index, color in enumerate(["green", "red", "black", "yellow"]):
			self.players.append(Player(color = color,
												id = index,
												start_field = start_field
												))
			
			## create Figure objects for each player (id range [1,4])
			for figure_num in range(4):
				figure = Figure(rel_pos = None,
								player = self.players[-1],
								id = figure_num)
				self.figures.append(figure)
				self.players[-1].figures.append(figure)
			start_field += 10

		## iterate through all players with their respective start_field index
		for index, player in enumerate(self.players):
			homefield = self.board_thread.home_fields[index]
			endfield = self.board_thread.end_fields[index]

			player.set_homefield(homefield)
			player.set_endfield(endfield)

	def gesture_should_game_quit(self):
		self.hand_thread.video_feed = "gesture"
		self.game_status = GameStatus.SHOULD_QUIT

		while True and not self.stopped():
			time.sleep(0.1)
			current_gesture = self.hand_thread.current_gesture
						
			if current_gesture == "thumbs up":
				self.game_status = GameStatus.QUIT
				return True
			elif current_gesture == "thumbs down":
				self.game_status = GameStatus.RUNNING
				return False

	def wait_for_gesture(self, goal_gesture, second_goal_gesture = None):
		self.hand_thread.video_feed = "gesture"
		last_gesture = self.hand_thread.current_gesture

		while True and not self.stopped():
			time.sleep(0.1)

			current_gesture = self.hand_thread.current_gesture
			if (current_gesture == "rock" and last_gesture == "peace") \
				or (current_gesture == "peace" and last_gesture == "rock"):
				quit = self.gesture_should_game_quit()
				if quit:
					return False

			if current_gesture != last_gesture and current_gesture == goal_gesture:
				return True
			elif second_goal_gesture is not None: 
				if current_gesture != last_gesture and current_gesture == second_goal_gesture:
					return False	
				else:
					last_gesture = current_gesture
			else:
				last_gesture = current_gesture

	def wait_for_count(self, possible_figure_ids):
		self.hand_thread.video_feed = "counter"
		last_count = self.hand_thread.current_count
		showed_ten = False
		while True and not self.stopped():
			time.sleep(0.1)

			if last_count == 10:
				showed_ten =True
			if showed_ten and self.hand_thread.current_count-1 in possible_figure_ids:
				return True
			else:
				last_count = self.hand_thread.current_count

	def current_turn(self, eye_count):
		player = self.players[self.current_player]

		available_figures = player.available_figures(eye_count)
		self.current_turn_available_figures = available_figures
		figure_ids = []
		for figure, id in available_figures:
			figure_ids.append(figure.id)

		if len(available_figures) > 0:
			figure_accepted = False
			while not figure_accepted and not self.stopped() and not self.game_status == GameStatus.QUIT:
				self.turn_status = TurnStatus.SELECT_FIGURE
				## Wenn Zug möglich, wähle einen aus
				chosen_figure = self.choose_figure(available_figures)
				self.turn_status = TurnStatus.SELECT_FIGURE_ACCEPT
				figure_accepted = self.wait_for_gesture("thumbs up", "thumbs down")

			## führe Zug aus
			if not self.stopped() and not self.game_status == GameStatus.QUIT:
				self.move(player, chosen_figure, eye_count)

		else:
			self.turn_status = TurnStatus.SELECT_FIGURE_SKIP
			self.wait_for_gesture("thumbs up")

	def move(self, p_current_player, p_chosen_figure, p_eye_count):
		if p_chosen_figure.rel_pos is not None:
			## remove figure from old field
			try:
				old_absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=p_chosen_figure.rel_pos)
				self.fields[old_absPos].figure = None
			except IndexError:
				## remove logic for endfield
				endfieldPos = p_chosen_figure.rel_pos % 40
				p_current_player.end_fields[endfieldPos].figure = p_chosen_figure
	
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
			field = p_current_player.end_fields[endfieldPos]
		field.figure = p_chosen_figure

		## set figure.rel_pos
		print(f"Moved {p_chosen_figure.id} to {newPos}")
		p_chosen_figure.set_position(newPos)

	def choose_figure(self, available_figures):
		current_figure_ids = []
		for figure in available_figures:
			current_figure_ids.append(figure[0].id)
		
		self.wait_for_count(current_figure_ids)
		
		player = self.players[self.current_player]
		chosen_figure = player.figures[self.hand_thread.current_count-1]
		self.selected_figure = chosen_figure
		return chosen_figure

	def calculate_new_pos(self, p_chosen_figure, p_eye_count):
		newPos = 0
		if  p_chosen_figure.rel_pos is not None:
			newPos = p_chosen_figure.rel_pos + p_eye_count
		return newPos
	
	def kick(self, absPos):
		if absPos > 39:
			return
	
		field = self.fields[absPos]
	
		if field.figure is not None:
			field.figure.set_position(None)
			self.turn_status = TurnStatus.KICK

	def normalize_position(self, p_player_id: int, p_position: int):
		"""Method to convert relative position to absolute

		This method takes a player id and the position of the player
		an normalises it for other methods such as kick.

		Args:
			p_player_id:	Id of player
			p_position:		Index of field

		Returns:
			Normalised index

		Example:	
			normalized = index of field from the perspective of the player 0

			player = 0; pos = 40
			normalized --> 0

			player = 1; pos = 0
			normalized --> 10
		"""
		# Used to catch bad inputs
		if p_position is None:
			raise IndexError
		if p_position > 39:
			raise IndexError

		# Modulo 40 is the number of fields on the board
		return (p_position + p_player_id * 10) % 40

	def get_status_by_player_id(self, player_id):
		""" Changes RoundStatus to current player

		Args:
			player_id:	Id of current player

		Returns:
			Fitting RoundStatus for player_id
		"""
		if player_id == 0:
			return RoundStatus.PLAYER_GREEN
		elif player_id == 1:
			return RoundStatus.PLAYER_RED
		elif player_id == 2:
			return RoundStatus.PLAYER_BLACK
		elif player_id == 3:
			return RoundStatus.PLAYER_YELLOW
		else:
			return None

	def stop(self):
		"""Method for stopping the thread."""
		self._stop_event.set()

	def stopped(self):
		"""Returns the status of thread."""
		return self._stop_event.is_set()
	
	def run(self):
		"""Gets called when game_thread is started and contains complete gamelogic

		This method gets called when game_thread.start() is called in the MainThread.
		It first creates the boardgame with the help of board_thread and saves the 
		corners of the board. It contains a while-loop where every loop is a full 
		game cicle for one player. It also updates the Game- Turn- and RoundStatus
		accordingly. It breaks when the GameStatus changes to quit or when the 
		thread is stopped.
		"""

		# Prepares the boardgame
		self.create_boardgame()

		# Saves corners for Ui board_frame transformations
		self.corners = self.board_thread.corners
		
		# Sets initialized flag to true updates GameStatus
		self.initialized = True
		self.game_status = GameStatus.START

		# Contains a loop which waits for the given gesture
		self.wait_for_gesture("thumbs up")

		# While-loop with cicle for one player
		while not self.stopped() and not self.game_status == GameStatus.QUIT:

			self.game_status = GameStatus.RUNNING			
			
			player = self.players[self.current_player]
			print(f"It's {player.color}'s turn!")

			# Updates GameStatus to the right team
			self.round_status = self.get_status_by_player_id(player.id)

			## if no figures are on the street and possible endfield figures are at the end
			if not player.has_movable_figures() and not self.game_status == GameStatus.QUIT:

				# Player has 3 tries to roll a 6
				for tries in range(4):
					
					# Prevents loop of thread when game ends here
					if self.stopped() or self.game_status == GameStatus.QUIT:
						break

					# Updates global tries variable for the ui
					self.current_try = tries
					self.turn_status = TurnStatus.ROLL_DICE_HOME

					# Skips if player used all tries
					if tries == 3:
						self.turn_status = TurnStatus.SELECT_FIGURE_SKIP
						self.wait_for_gesture("thumbs up")
						break
					
					# Waits for gesture and saves current_eye_count when the loop breaks
					self.wait_for_gesture("thumbs up")
					eye_count = self.dice_thread.current_eye_count
					self.current_turn_eye_count = eye_count
					
					# Enters the players turn if a 6 is rolled
					if eye_count == 6 and not self.game_status == GameStatus.QUIT:
						self.current_turn(eye_count)
						break
			
			# Gets entered if player has 1 or more figures outside the house 
			while player.has_movable_figures() and not self.stopped() and not self.game_status == GameStatus.QUIT:

				# Waits for gesture and saves current_eye_count when the loop breaks
				self.turn_status = TurnStatus.ROLL_DICE
				self.wait_for_gesture("thumbs up")
				eye_count = self.dice_thread.current_eye_count
				self.current_turn_eye_count = eye_count
				
				# Enters turn logic
				self.current_turn(eye_count)

				# Lets the player roll again if he rolled a 6
				if eye_count != 6:
					break

			# Updates the loop to the next player, if current player didn't finish 
			if not player.all_figures_finished():
				self.current_player = (self.current_player + 1) %4
			
			# Game finished and can be quit
			else:
				self.game_status = GameStatus.FINISHED
				self.wait_for_gesture("rock")
				self.game_status = GameStatus.SHOULD_QUIT
				self.wait_for_gesture("thumbs up")
				self.game_status = GameStatus.QUIT

			# Loop breaks if game_thread is stopped
			if self.stopped():
				break

		
