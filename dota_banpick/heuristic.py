'''
File Created: Tuesday, 17th October 2023 1:50:45 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Tuesday, 17th October 2023 2:12:06 pm
Modified By: Sukai Huang (huangsukai1997@gmail.com>)
-----
Copyright 2023 - 2023 by Sukai@Community Project
All rights reserved.
This file is part of The DOTA 2 BanPick Tool Project,
and is released under The MIT License. Please see the LICENSE
file that should have been included as part of this project.
'''

# this file implements the advantage score computation method

import copy
from glob import glob
import os

from natsort import natsorted
from tqdm.auto import tqdm
from dota_banpick.config import *
from dota_banpick.pickaction import StateNode
import logging
import numpy as np
import itertools
import pickle


def calculate_heuristic(ally_hero_list, opponent_hero_list,
                        counter_weight=COUNTER_WEIGHT,
                        counter_temperature_list=COUNTER_TEMPERATURE_LIST

                        ):
    """it will return the advantage value for your team. 
    Your team's goal is to maximise it, while the opponent team's goal is to minimise it
    versus_matrix should be counter rate matrix 

    Args:
        statenode (StateNode): _description_
        versus_matrix (_type_): counter rate matrix
        with_winrate_matrix (_type_): _description_
        counter_weight (_type_, optional): _description_. Defaults to COUNTER_WEIGHT.
        pos_1_counter_temperature (_type_, optional): _description_. Defaults to POS_1_COUNTER_TEMPERATURE.
        pos_2_counter_temperature (_type_, optional): _description_. Defaults to POS_2_COUNTER_TEMPERATURE.
        pos_3_counter_temperature (_type_, optional): _description_. Defaults to POS_3_COUNTER_TEMPERATURE.
        pos_4_counter_temperature (_type_, optional): _description_. Defaults to POS_4_COUNTER_TEMPERATURE.
        pos_5_counter_temperature (_type_, optional): _description_. Defaults to POS_5_COUNTER_TEMPERATURE.

    Returns:
        float: numeric score
    """

    # for versus
    if opponent_hero_list.count(None) == 5:
        global_vs_winrate = 0.5
    else:
        global_versus_winrate_lst = []
        for ally_pos_ind, ally_hero in enumerate(ally_hero_list):
            if ally_hero is not None:
                local_versus_winrate_lst = []
                for oppo_pos_ind, oppo_hero in enumerate(opponent_hero_list):
                    if oppo_hero is not None:
                        score = counter_rate_matrix[ally_hero][oppo_hero] * \
                            counter_weight
                        score = score * \
                            counter_temperature_list[ally_pos_ind][oppo_pos_ind]
                        score = score + 0.5  # 0.5 as base
                        local_versus_winrate_lst.append(score)
                if len(local_versus_winrate_lst) > 0:
                    local_vs_winrate = np.mean(local_versus_winrate_lst)
                else:
                    local_vs_winrate = 0.5
                global_versus_winrate_lst.append(local_vs_winrate)
        if len(global_versus_winrate_lst) > 0:
            global_vs_winrate = np.mean(global_versus_winrate_lst)
        else:
            global_vs_winrate = 0.5

    # for with
    global_with_winrate_lst = []
    available_heros = [h for h in ally_hero_list if h is not None]
    combination_list = list(itertools.combinations(available_heros, 2))
    for combi in combination_list:
        score = with_winrate_matrix[combi[0]][combi[1]]
        global_with_winrate_lst.append(score)

    if len(global_with_winrate_lst) > 0:
        global_with_winrate = np.mean(global_with_winrate_lst)
    else:
        global_with_winrate = 0.5

    heuristic = np.mean([global_vs_winrate, global_with_winrate])

    return heuristic


def compute_bad_picks_for_each_pos(statenode: StateNode,
                                   display_num=4):
    # output structure : {pos: [bad_hero_ele,]}
    # give a list of heros that the opponent may counter you most

    # filter available hero pools
    hero_pool_lst = statenode.ally_hero_pools
    opponent_hero_list = statenode.opponent_heros
    opponent_hero_list = [h for h in opponent_hero_list if h is not None]
    if len(opponent_hero_list) == 0:
        return None

    filtered_hero_pool_lst = []
    for pool in hero_pool_lst:
        pool_copy = copy.deepcopy(pool)  # type: list
        for unavailable_hero in statenode.ban_lst:
            if unavailable_hero in pool_copy:
                pool_copy.remove(unavailable_hero)
        filtered_hero_pool_lst.append(pool_copy)
    

    # calculate versus rate
    output_dict = dict()  # {dota_position: [bad_heros]}
    for pos_ind, pos_hero_pool in enumerate(filtered_hero_pool_lst):
        hero_counterrate_tuple_list = []  # [(hero, local_vs_winrate)]
        for hero in pos_hero_pool:
            # cal versus winrate
            
            local_vs_counterrate_lst = [
                counter_rate_matrix[hero][oppo_hero] for oppo_hero in opponent_hero_list]
            local_vs_counterrate = np.mean(local_vs_counterrate_lst)
            hero_counterrate_tuple_list.append((hero, local_vs_counterrate))
        # once we get hero_winrate_tuple_list, we sort it and get display_num of it
        
        hero_counterrate_tuple_list_trunc = sorted(
            hero_counterrate_tuple_list, key=lambda x: x[1])[:display_num]
        output_dict[pos_ind+1] = [x[0]
                                  for x in hero_counterrate_tuple_list_trunc]

    return output_dict


def compute_associated_ban_suggestion_first_round(suggested_hero_pick_dict):
    # suggested_hero_pick_dict[str_pick_choice] = updated_suggested_hero_list
    # output structure : suggested_hero_ban_dict[str_pick_choice] = suggested_ban_hero_list
    suggested_hero_ban_dict = dict()
    for str_pick_choice, suggested_hero_list in suggested_hero_pick_dict.items():
        suggested_ban_hero_list = []
        pos_choices = eval(str_pick_choice)
        if pos_choices not in FIRST_ROUND_PICK_CHOICE:
            # assert RuntimeError("Not getting first round pos choice")
            counter_poses = [3,4]
        else:
            pos_choices_ind = FIRST_ROUND_PICK_CHOICE.index(pos_choices)
            counter_poses = FIRST_ROUND_COUNTER_CHOICE[pos_choices_ind]

        counter_pos_hero_combos = [(x, y) for x in default_hero_pools[counter_poses[0] - 1]
                                   for y in default_hero_pools[counter_poses[1] - 1] if x != y]
        for our_combo, _ in suggested_hero_list:
            counter_max_score = -999
            counter_max_ind = -999
            for oppo_ind, oppo_combo in enumerate(counter_pos_hero_combos):
                if oppo_combo[0] in our_combo or oppo_combo[1] in our_combo:
                    continue

                score = counter_rate_matrix[oppo_combo[0]][our_combo[0]] * BAN_SUGGEST_FRONT_POS_COUTNER_WEIGHT * \
                    BAN_SUGGEST_FRONT_POS_COUTNER_WEIGHT  # pos at front is more significant, thus weigh more
                score += counter_rate_matrix[oppo_combo[0]][our_combo[1]]
                score += counter_rate_matrix[oppo_combo[1]
                                             ][our_combo[0]] * BAN_SUGGEST_FRONT_POS_COUTNER_WEIGHT
                score += counter_rate_matrix[oppo_combo[1]][our_combo[1]]

                if counter_max_score < score:
                    counter_max_score = score
                    counter_max_ind = oppo_ind
            suggested_ban_hero_list.append(
                counter_pos_hero_combos[counter_max_ind])
        suggested_hero_ban_dict[str_pick_choice] = suggested_ban_hero_list

    return suggested_hero_ban_dict


if __name__ == "__main__":
    # debug
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

    hero_pool_fps = glob(os.path.join(
        record_folder, "default_pos_*_hero_pool.txt"))
    hero_pool_fps = natsorted(hero_pool_fps)
    ally_hero_pools = []
    opponent_hero_pools = []
    for hp_fp in hero_pool_fps:
        with open(hp_fp, 'r') as f:
            hp_text = f.read()
            ally_hero_pools.append(eval(hp_text))
            opponent_hero_pools.append(eval(hp_text))

    start_node = StateNode(*ally_hero_pools, *opponent_hero_pools)
    start_node.add_hero('Earthshaker',True,2)
    start_node.add_hero('Faceless Void',True,1)
    start_node.add_hero('Lone Druid',False,2)
    start_node.add_hero('Ancient Apparition',False,5)

    compute_bad_picks_for_each_pos(start_node)
# {1: ['Arc Warden', 'Alchemist', 'Anti-Mage', 'Spectre'],
#  2: ['Pugna', 'Alchemist', 'Huskar', 'Anti-Mage'],
#  3: ['Abaddon', 'Night Stalker', 'Legion Commander', 'Huskar'],
#  4: ['Io', 'Disruptor', 'Pugna', 'Grimstroke'],
#  5: ['Abaddon', 'Io', 'Disruptor', 'Pugna']}
