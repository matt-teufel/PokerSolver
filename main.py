from pypokerengine.api.game import setup_config, start_poker
from poker_bot import PokerAI
from fishplayer import FishPlayer

config = setup_config(max_round=10, initial_stack=20000, small_blind_amount=10)
config.register_player(name="AI Bot", algorithm=PokerAI())
config.register_player(name="Fish Player", algorithm=FishPlayer())
game_result = start_poker(config, verbose=1)
