from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.poker_constants import PokerConstants as Const
import json
from poker_bot_constants import *
import random


class PokerAI(
    BasePokerPlayer
):  # Do not forget to make parent class as "BasePokerPlayer"
    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        pos = False
        hero = round_state["seats"][0]  # our ai bot
        villain = round_state["seats"][1]  # opponent
        pot_size = round_state["pot"]["main"]["amount"]
        big_blind_size = round_state["small_blind_amount"] * 2
        effective_stack = min(
            hero["stack"], villain["stack"]
        )  # the amount of chips actually in play
        bbs = effective_stack / big_blind_size
        spr = effective_stack / pot_size  # stack to pot ratio
        file_name = "./ranges/"
        if (
            round_state["dealer_btn"] == round_state["next_player"]
        ):  # we are next player, check if we are in position
            pos = True
        if pos:
            file_name += "bb/"
        else:
            file_name += "sb/"

        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        print("======================")
        print(hole_card)
        print(round_state)
        print(valid_actions)
        print("round state " + round_state["street"])
        converted_hole_cards = convert_hole_cards(hole_card)
        if round_state["street"] == "preflop":
            print("PREFLOP")
            # check for allin
            closest_chart = find_closest_chart(bbs)
            print("closest chart: " + str(closest_chart))
            file_name += str(closest_chart) + "/"
            history = round_state["action_histories"]["preflop"]
            if pos:  # we are in position -- we are big blind
                print("we are big blind")
                if (
                    spr < 3 or len(history) > 5
                ):  # if spr is low or we are in 4 bet spot, treat it as ALL IN
                    file_name += ALL_IN
                    ## ToDo add better 4 bet handling by using previous raise range
                    if len(valid_actions) == 2:
                        max_bet = valid_actions[1]["amount"]
                    else:
                        max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 3:  # single raise pot
                    file_name += SINGLE_RAISE
                    max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 5:  # 3 bet pot
                    file_name += THREE_BET_RESPONSE
                    max_bet = valid_actions[2]["amount"]["max"]
                action = lookup_hand_action(file_name, converted_hole_cards)
            else:  # we are not in position -- we are small blind
                print("we are small blind")
                if (
                    spr < 3 or len(history) > 4
                ):  # if spr is low or we are in 4 bet, treat as all in
                    file_name += ALL_IN
                    if len(valid_actions) == 2:
                        max_bet = valid_actions[1]["amount"]
                    else:
                        max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 2:  # we are opening
                    file_name += OPEN
                    max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 4:  # we are making 3 betting decision
                    file_name += THREE_BET
                action = lookup_hand_action(file_name, converted_hole_cards)
            return handle_action_preflop(
                action, valid_actions, pot_size, max_bet, big_blind_size, pos
            )
        print("======================")

        return action, amount  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def find_closest_chart(bbs: int):
    closest_number = CHARTS[0]
    for num in CHARTS:
        if abs(bbs - num) < abs(bbs - closest_number):
            closest_number = num
    return closest_number


def lookup_hand_action(file_name: str, converted_hole_cards: str):
    print("opening file: " + file_name)
    hole_card_index = COMBOS.index(converted_hole_cards)
    actions = []
    weights = []
    with open(file_name) as json_file:
        data = json.load(json_file)
        for solution in data["solutions"]:
            actions.append(solution["action"]["code"])
            weights.append(solution["strategy"][hole_card_index])
    selected_action = random.choices(actions, weights=weights, k=1)[0]
    print("actions: " + str(actions))
    print("weights: " + str(weights))
    print("selected action: " + str(selected_action))
    return selected_action


def convert_hole_cards(hole_cards: list):
    if hole_cards[0][1] == hole_cards[1][1]:
        print("hole cards are a pocket pair")
        return hole_cards[0][1] + hole_cards[1][1]

    if CARD_ORDER.index(hole_cards[0][1]) < CARD_ORDER.index(hole_cards[1][1]):
        converted_hole_cards = hole_cards[0][1] + hole_cards[1][1]
    else:
        converted_hole_cards = hole_cards[1][1] + hole_cards[0][1]

    if hole_cards[0][0] == hole_cards[1][0]:
        print("suited hand")
        converted_hole_cards += "s"
    else:
        print("offsuit hand")
        converted_hole_cards += "o"
    print("converted hole cards: " + converted_hole_cards)
    return converted_hole_cards


# def create_combos_list():
#     with open("./ranges/sb/20/allin.json") as json_file:
#         data = json.load(json_file)
#         for combo in data["players_info"][0]["simple_hand_counters"]:
#             COMBOS.append(combo)
#     print(COMBOS)


def handle_action_preflop(
    action: str,
    valid_actions: list,
    pot_size: int,
    max_bet: int,
    big_blind_size: int,
    pos: bool,
):
    if action == "F":
        if pos and valid_actions[1]["amount"] == big_blind_size:
            # don't fold if we can check our option as big blind
            return "call", big_blind_size
        else:
            return "fold", 0
    elif action == "C":
        return "call", valid_actions[1]["amount"]
    elif action == "RAI":
        return "raise", max_bet
    else:
        raise_size = pot_size * 3
        if raise_size > max_bet:
            raise_size = max_bet
        return "raise", raise_size
