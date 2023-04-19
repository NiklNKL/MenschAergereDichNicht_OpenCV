import threading
import cv2
from game_objects import Field, Player, Figure
from utilities import GameStatus, RoundStatus, TurnStatus
import time

class Game(threading.Thread):
	def __init__(self, dice_thread, hand_thread, board_thread) -> None:

		threading.Thread.__init__(self)

		self.corners = board_thread.corners
		
		self.fields = []
		self.figures = []
		self.players = []
		self.current_player = 0

		self.selected_figure = 0
		self.current_turn_eye_count = 0
		self.current_turn_available_figures = []

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
				figure = Figure(relPos = None,
								player = self.players[-1],
								id = figure_num)
				self.figures.append(figure)
				self.players[-1].figures.append(figure)
			start_field += 10
		
		## move green's figure 1 to absPos 36 to test end_fields
		#self.fields[36].figure = self.players[0].figures[0]
		#self.players[0].figures[0].set_position(36)

		## move yellow's figure 1 to absPos 6 to test kick logic
		#self.GameHandler.players[-1].figures[0].set_position(16)
		#self.GameHandler.fields[6].figure = self.GameHandler.players[-1].figures[0]

		## iterate through all players with their respective start_field index
		for index, player in enumerate(self.players):
			homefield = self.board_thread.home_fields[index]
			endfield = self.board_thread.end_fields[index]

			player.set_homefield(homefield)
			player.set_endfield(endfield)

		for figure in self.figures:
			for count in range(0,4):
				pass
				# UiHandler.highlighting(figure.player.home_fields[count].img_pos, figure.id, figure.player.color)

		## check if everything was created correctly
		# for field in self.fields:
		# 	print({"img_pos": field.img_pos, "figure": field.figure, "street_index": field.street_index})
		# for player in self.players:
		# 	print({"color": player.color, "start_field": player.start_field, "finish_field": player.finish_field})
		# for figure in self.figures:
		# 	print({"relPos": figure.relPos, "team": figure.player, "item": figure.id})
		# print("finished preparations")

	def wait_for_gesture(self, goal_gesture, second_goal_gesture = None):
		self.hand_thread.video_feed = "gesture"
		last_gesture = self.hand_thread.current_class

		while True and not self.stopped():
			time.sleep(0.1)
			current_gesture = self.hand_thread.current_class
			if current_gesture != last_gesture and current_gesture == goal_gesture:
				return True
			else:
					last_gesture = current_gesture
			if second_goal_gesture is not None: 
				if current_gesture != last_gesture and current_gesture == second_goal_gesture:
					return False
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
			while not figure_accepted and not self.stopped():
				self.turn_status = TurnStatus.SELECT_FIGURE
				## Wenn Zug möglich, wähle einen aus
				chosen_figure = self.choose_figure(available_figures)
				self.turn_status = TurnStatus.SELECT_FIGURE_ACCEPT
				figure_accepted = self.wait_for_gesture("thumbs up", "thumbs down")

			self.turn_status = TurnStatus.MOVE_FIGURE
			self.wait_for_gesture("thumbs up")
			## führe Zug aus
			self.move(player, chosen_figure, eye_count)
		else:
			self.turn_status = TurnStatus.SELECT_FIGURE_SKIP
			self.wait_for_gesture("thumbs up")

	def move(self, p_current_player, p_chosen_figure, p_eye_count):
		if p_chosen_figure.relPos is not None:
			## remove figure from old field
			try:
				old_absPos = self.normalize_position(p_player_id=p_current_player.id, p_position=p_chosen_figure.relPos)
				self.fields[old_absPos].figure = None
			except IndexError:
				## remove logic for endfield
				endfieldPos = p_chosen_figure.relPos % 40
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

		## set figure.relPos
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
		# chosen_figure = self.hand_thread.current_count-1
		
		# # return chosen figure object
		# return available_figures[chosen_figure][0]

		# Wir zeigen 2 an
		# Wir haben auch nur 2 zur Auswahl, heißt die ist in available_figures index 0


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
			field.figure.set_position(None, field.img_pos, field.figure.player.color, field.figure.id)
			self.turn_status = TurnStatus.KICK

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

	def get_status_by_player_id(self, player_id):
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
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()
	
	def run(self):

		self.create_boardgame()
		
		self.initialized = True
		self.game_status = GameStatus.START

		self.wait_for_gesture("thumbs up")

		self.game_status = GameStatus.RUNNING

		while True and not self.stopped():
			
			player = self.players[self.current_player]
			print(f"It's {player.color}'s turn!")

			self.round_status = self.get_status_by_player_id(player.id)

			self.turn_status = TurnStatus.PLAYER_READY
			self.wait_for_gesture("thumbs up")

			

			## if no figures are on the street and possible endfield figures are at the end
			if not player.has_movable_figures():
				for turn in range(4):
					self.turn_status = TurnStatus.ROLL_DICE
					if turn == 3:
						self.turn_status.SELECT_FIGURE_SKIP
						self.wait_for_gesture("thumbs up")
						break

					self.wait_for_gesture("thumbs up")
					eye_count = self.dice_thread.current_eye_count
					self.current_turn_eye_count = eye_count
					
					if eye_count == 6:
						self.current_turn(eye_count)
						break
			
			while player.has_movable_figures() and not self.stopped():
				self.turn_status = TurnStatus.ROLL_DICE
				self.wait_for_gesture("thumbs up")
				eye_count = self.dice_thread.current_eye_count
				self.current_turn_eye_count = eye_count
				
				self.current_turn(eye_count)
				if eye_count != 6:
					break
			 
			if not player.all_figures_finished():
				self.current_player = (self.current_player + 1) %4
			else:
				self.game_status = GameStatus.FINISHED
				self.wait_for_gesture("peace")
				self.game_status = GameStatus.SHOULD_QUIT
				self.wait_for_gesture("thumbs up")
				self.game_status = GameStatus.QUIT

			if self.stopped():
				break

		
