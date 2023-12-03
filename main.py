from pypokerengine.api.game import setup_config, start_poker
from poker_bot import PokerAI
from fishplayer import FishPlayer
from randomplayer import RandomPlayer
from honestplayer import HonestPlayer
from allinplayer import AllinPlayer
import matplotlib as plt


player_pool = [
    ["Allin Player", AllinPlayer()],
    ["Fish Player", FishPlayer()],
    ["Random Player", RandomPlayer()],
    ["Honest Player", HonestPlayer()],
]

initial_stacks = [200, 1000, 2000, 6000]  # 20 bbs, 50 bbs, 100 bbs, 300 bbs
stack_sizes = [stack / 20 for stack in initial_stacks]

for challenger in player_pool:
    average_bbs = []
    for stack_size in initial_stacks:
        average_winnings = 0
        for i in range(5):
            print("current challenger: ", challenger[0], " stack size: ", stack_size)
            config = setup_config(
                max_round=100, initial_stack=stack_size, small_blind_amount=10
            )
            config.register_player(name="AI Bot", algorithm=PokerAI())
            config.register_player(name=challenger[0], algorithm=challenger[1])
            game_result = start_poker(config, verbose=1)
            print("game result", game_result)
            hero_stack = game_result["players"][0]["stack"]
            big_blinds_won = hero_stack / (20)
            average_winnings += big_blinds_won
        average_bbs_per_100 = average_winnings / 5
        average_bbs.append(average_bbs_per_100)
    plt.plot(stack_sizes, average_bbs, label=challenger[0])

plt.xlabel("Stack Size")
plt.ylabel("Average Big Blinds Won Per 100 Rounds")
plt.title("Average Big Blinds Won Per 100 Rounds for each challenger")
plt.legend()
plt.show()
