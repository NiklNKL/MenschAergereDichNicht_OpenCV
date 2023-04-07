
fields = []
figures = []
players = []
current_player = 0

def play_whole_turn(LogicHandler) -> int:
	global players
	global current_player
	p = players[current_player]
	print(f"It's {p}'s turn!")
	
	LogicHandler.UiHandler.update_text(player=p.color)

	## if no figures are on the street and possible endfield figures are at the end
	if not p.has_movable_figures():
		for turn in range(3):
			try:
				eye_count = LogicHandler.get_current_dice()
			except Exception as e:
				print(e)
				return 1
			
			LogicHandler.UiHandler.update_text(dice=eye_count, turn=turn+1)

			if eye_count == 6:
				current_turn(LogicHandler, eye_count)
				break

	while p.has_movable_figures():
		try:
			eye_count = LogicHandler.get_current_dice()
		except Exception as e:
			print(e)
			return 1

		current_turn(LogicHandler, eye_count)
		if eye_count != 6:
			break
	
	status = p.check_all_finish()
	if status != 1:
		current_player = (current_player + 1) %4

	return status

def current_turn(LogicHandler, eye_count):
	p = players[current_player]

	avail_moves = p.available_moves(eye_count, LogicHandler.UiHandler)
	if len(avail_moves) > 0: 
		## Wenn Zug möglich, wähle einen aus
		chosen_figure = LogicHandler.choose_move(avail_moves)
		## führe Zug aus
		move(p, chosen_figure, eye_count, LogicHandler.UiHandler)

def move(p_current_player, p_chosen_figure, p_eye_count, UiHandler):
	global fields

	if p_chosen_figure.relPos is not None:
		## remove figure from old field
		old_absPos = normalize_position(p_player_id=p_current_player.id, p_position=p_chosen_figure.relPos)
		fields[old_absPos].figure = None
	
	##new relative pos
	newPos = calculate_new_pos(p_chosen_figure, p_eye_count)
	
	##set field.figure
	try:
		##new abs pos
		absPos = normalize_position(p_player_id=p_current_player.id, p_position=newPos)
		
		kick(absPos, UiHandler)

		field = fields[absPos]
		field.figure = p_chosen_figure
		print(f"NewPos: {newPos}")
		print(f"AbsPos: {absPos}")
	except IndexError:
		## move into endfield
		endfieldPos = newPos % 40
		p_current_player.endfields[endfieldPos].figure = p_chosen_figure

	## set figure.relPos
	print(f"Moved {p_chosen_figure.id} to {newPos}")
	p_chosen_figure.set_position(newPos, field.imgPos, p_current_player.color, p_chosen_figure.id ,UiHandler)

def calculate_new_pos(p_chosen_figure, p_eye_count):
	newPos = 0
	if  p_chosen_figure.relPos is not None:
		newPos = p_chosen_figure.relPos + p_eye_count
	return newPos
	
def kick(absPos, UiHandler):
	global fields

	if absPos > 39:
		return
	
	field = fields[absPos]
	
	if field.figure is not None:
		field.figure.set_position(None, field.imgPos, field.figure.player.color, field.figure.id, UiHandler)
		UiHandler.update_text(prompt=f"figure {field.figure} got kicked!")

def normalize_position(p_player_id, p_position):
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

