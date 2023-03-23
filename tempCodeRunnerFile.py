f_normalized_position = (((p_player.get_id() *10) + available_figures[0].get_id() + p_eye_count)) % 40
                for p2 in self.current_players:
                    for f2 in p2.get_figures():
                        if (f2.get_position() != None) & (p2.get_id() != p_player.get_id()):
                            f2_normalized_position = (( (p2.get_id() *10) + f2.get_position())) % 40
                            if f_normalized_position == f2_normalized_position:
                                f2.set_position(None)