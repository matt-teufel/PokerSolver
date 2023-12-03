from pypokerengine.players import BasePokerPlayer
from pypokerengine.engine.poker_constants import PokerConstants as Const
import json
from poker_bot_constants import *
import random
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

hero_range = []
villain_range = []


class PokerAI(
    BasePokerPlayer
):  # Do not forget to make parent class as "BasePokerPlayer"
    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        global hero_range
        global villain_range
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
        hero_file_name = "./ranges/"
        villain_file_name = "./ranges/"
        if (
            round_state["dealer_btn"] == round_state["next_player"]
        ):  # we are next player, check if we are in position
            pos = True
        if pos:
            hero_file_name += "bb/"
            villain_file_name += "sb/"
        else:
            hero_file_name += "sb/"
            villain_file_name += "bb/"

        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        print("======================")
        print(hole_card)
        print(round_state)
        print(valid_actions)
        print("round state " + round_state["street"])
        converted_hole_cards = convert_hole_cards(hole_card)
        community_cards = round_state["community_card"]
        if round_state["street"] == "preflop":
            # check for allin
            closest_chart = find_closest_chart(bbs)
            print("closest chart: " + str(closest_chart))
            hero_file_name += str(closest_chart) + "/"
            villain_file_name += str(closest_chart) + "/"
            history = round_state["action_histories"]["preflop"]
            if pos:  # we are in position -- we are big blind
                print("we are big blind")
                if (
                    spr < 3 or len(history) > 5
                ):  # if spr is low or we are in 4 bet spot, treat it as ALL IN
                    hero_file_name += ALL_IN
                    villain_file_name += ALL_IN
                    villain_action = "RAI"
                    ## ToDo add better 4 bet handling by using previous raise range
                    if len(valid_actions) == 2:
                        max_bet = valid_actions[1]["amount"]
                    else:
                        max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 3:  # single raise pot
                    hero_file_name += SINGLE_RAISE
                    villain_file_name += OPEN
                    villain_action = "R"
                    max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 5:  # 3 bet pot
                    hero_file_name += THREE_BET_RESPONSE
                    villain_file_name += THREE_BET
                    villain_action = "R"
                    max_bet = valid_actions[2]["amount"]["max"]
                with open(hero_file_name) as json_file:
                    chart = json.load(json_file)
                    action = lookup_hand_action(chart, converted_hole_cards)
                    hero_range = construct_preflop_range(chart, action)
                with open(villain_file_name) as f:
                    villain_chart = json.load(f)
                    villain_range = construct_preflop_range(
                        villain_chart, villain_action
                    )
            else:  # we are not in position -- we are small blind
                print("we are small blind")
                if (
                    spr < 3 or len(history) > 4
                ):  # if spr is low or we are in 4 bet, treat as all in
                    hero_file_name += ALL_IN
                    villain_file_name += ALL_IN
                    villain_action = "RAI"
                    if len(valid_actions) == 2:
                        max_bet = valid_actions[1]["amount"]  # max call
                    else:
                        max_bet = valid_actions[2]["amount"]["max"]  # max raise
                elif len(history) == 2:  # we are opening
                    hero_file_name += OPEN
                    villain_file_name += SINGLE_RAISE
                    villain_action = "C"
                    max_bet = valid_actions[2]["amount"]["max"]
                elif len(history) == 4:  # we are making 3 betting decision
                    hero_file_name += THREE_BET
                    max_bet = valid_actions[2]["amount"]["max"]
                    villain_file_name = THREE_BET_RESPONSE
                    villain_action = "C"
                with open(hero_file_name) as json_file:
                    chart = json.load(json_file)
                    action = lookup_hand_action(chart, converted_hole_cards)
                    hero_range = construct_preflop_range(chart, action)
                with open(villain_file_name) as f:
                    villain_chart = json.load(f)
                    villain_range = construct_preflop_range(
                        villain_chart, villain_action
                    )

            return handle_action_preflop(
                action, valid_actions, pot_size, max_bet, big_blind_size, pos
            )
        elif round_state["street"] == "flop":
            print("playing the flop")
            print("current hero range", hero_range)
            hero_range_strength = calculate_range_strength(hero_range, community_cards)
            villain_range_strength = calculate_range_strength(
                villain_range, community_cards
            )
            print("hero range strength ", hero_range_strength)
            print("villain range strength ", villain_range_strength)
            hole_card_strength = estimate_hole_card_win_rate(
                1000, 2, gen_cards(hole_card), gen_cards(community_cards)
            )
            print("hero hole card strength ", hole_card_strength)
            ## construct our opponent range from preflop history
            preflop_history = round_state["action_histories"]["preflop"]
        print("======================")

        return action, amount  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        print("round start message ")
        global hero_range
        global villain_range
        hero_range = []
        villain_range = []
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


def lookup_hand_action(chart, converted_hole_cards: str):
    hole_card_index = COMBOS.index(converted_hole_cards)
    actions = []
    weights = []
    for solution in chart["solutions"]:
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


def construct_preflop_range(chart, action: str):
    current_range = []
    total_weight = 0
    for solution in chart["solutions"]:
        current_action = solution["action"]["code"]
        if current_action == action or (
            action == "R" and current_action != "RAI" and "R" in current_action
        ):  # fix this logic later
            # extract the range from here
            print(COMBOS)
            for i in range(len(COMBOS)):
                current_weight = COMBO_WEIGHTS[i] * solution["strategy"][i]
                if (
                    current_weight > 0.25
                ):  # don't add to our range if it is insignificantly small
                    current_range.append([COMBOS[i], current_weight])
                    total_weight += current_weight
    return current_range


def calculate_range_strength(current_range, community_cards):
    # ToDo add logic to handle flushes. They are being ignored for the most part rn
    range_strength = 0
    perm_total = 0
    for combo in current_range:
        # need to turn the converted combo back into PyPokerEngine format for hand strenght calc
        if len(combo[0]) == 2:
            permutations, adjusted_weight = generate_pocket_pairs(
                combo[0][0], community_cards, combo[1]
            )
        elif combo[0][2] == "s":
            permutations, adjusted_weight = generate_suited_combos(
                combo[0], community_cards, combo[1]
            )
        else:
            permutations, adjusted_weight = generate_offsuit_combos(
                combo[0], community_cards, combo[1]
            )
        for perm in permutations:
            hand_strength = estimate_hole_card_win_rate(
                nb_simulation=100,
                nb_player=2,
                hole_card=gen_cards(perm),
                community_card=gen_cards(community_cards),
            )
            perm_total += 1
            range_strength += hand_strength * adjusted_weight / len(permutations)
    return range_strength / perm_total


def generate_pocket_pairs(num, community_cards, weight):
    pocket_pairs = []
    for i in range(len(SUITS)):
        for j in range(i, len(SUITS)):
            if i != j:
                pair = [SUITS[i] + num, SUITS[j] + num]
                if pair[0] not in community_cards and pair[1] not in community_cards:
                    pocket_pairs.append(pair)
    return (
        pocket_pairs,
        weight * len(pocket_pairs) / 6,
    )  # adjust the weight based off comm cards


def generate_offsuit_combos(combo, community_cards, weight):
    offsuit_combos = []
    for i in range(len(SUITS)):
        for j in range(len(SUITS)):
            if i != j:
                perm = [SUITS[i] + combo[0], SUITS[j] + combo[1]]
                if perm[0] not in community_cards and perm[1] not in community_cards:
                    offsuit_combos.append(perm)
    return offsuit_combos, weight * len(offsuit_combos) / 12


def generate_suited_combos(combo, community_cards, weight):
    suited_combos = []
    for i in range(len(SUITS)):
        perm = [SUITS[i] + combo[0], SUITS[i] + combo[1]]
        if perm[0] not in community_cards and perm[1] not in community_cards:
            suited_combos.append(perm)
    return suited_combos, weight * len(suited_combos) / 4


# def create_combos_list():
#     with open("./ranges/sb/20/allin.json") as json_file:
#         data = json.load(json_file)
#         for combo in data["players_info"][0]["simple_hand_counters"]:
#             COMBOS.append(combo)
#     print(COMBOS)


# combo_weights = []
# for i in range(len(COMBOS)):
#     current_combo = COMBOS[i]
#     if len(current_combo) == 2:
#         combo_weights.append(6)
#     elif current_combo[2] == "s":
#         combo_weights.append(4)
#     else:
#         combo_weights.append(12)
# print(combo_weights)
