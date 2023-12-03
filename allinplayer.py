from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 1000


class AllinPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        if len(valid_actions) == 2:
            return valid_actions[1]["action"], valid_actions[1]["amount"]
        else:
            return valid_actions[2]["action"], valid_actions[2]["amount"]["max"]

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info["player_num"]

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass
