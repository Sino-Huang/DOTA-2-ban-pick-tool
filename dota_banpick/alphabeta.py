'''
File Created: Tuesday, 17th October 2023 1:50:54 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Tuesday, 17th October 2023 2:11:39 pm
Modified By: Sukai Huang (huangsukai1997@gmail.com>)
-----
Copyright 2023 - 2023 by Sukai@Community Project
All rights reserved.
This file is part of The DOTA 2 BanPick Tool Project,
and is released under The MIT License. Please see the LICENSE
file that should have been included as part of this project.
'''
from glob import glob
import logging
import os
import pickle

from natsort import natsorted
from config import DEPTH_LIMIT, SUGGESTION_NUM
from pickaction import StateNode
from heuristic import calculate_heuristic
from tqdm.auto import tqdm
from multiprocessing import Manager, Pool
from tqdm.contrib.concurrent import process_map
from multiprocessing import Pool, Process, Manager, Lock

# this file implements the alpha beta pruning method

# need a function to detect whether need to run alpha beta


class BetaCutOffException(Exception):
    pass


def support_map_func(args):
    # ! need manager
    next_node, local_node_ind, depth, alpha, beta, cache_dict, suggested_hero_list, next_node_values_list, pick_choice_combo_dict, str_pick_choice = args
    next_node_value, _ = alphabeta(
        next_node, depth + 1, alpha, beta, False, cache_dict)
    next_node_values_list.append(next_node_value)
    suggested_hero_list.append((pick_choice_combo_dict[str_pick_choice][local_node_ind], next_node_value))
    
    if next_node_value > beta:
        raise BetaCutOffException


def alphabeta(node: StateNode, depth, alpha, beta, is_maximizing_player, cache_dict):
    global versus_winrate_matrix
    global with_winrate_matrix
    global counter_rate_matrix

    if str(node) in cache_dict:
        return cache_dict[str(node)]

    if depth > DEPTH_LIMIT or node.is_terminated():
        value = calculate_heuristic(
            node, counter_rate_matrix, with_winrate_matrix)
        cache_dict[str(node)] = (value, None)
        return value, None

    output_next_nodes_dict, pick_choice_combo_dict = node.next_possible_nodes()

    if is_maximizing_player:  # need to output desired list
        value = -9999
        break_flag = False
        # structure {str_pick_choice: [(hero_1, hero_2)]}
        suggested_hero_pick_dict = dict()

        # get child nodes
        # output_next_nodes_dict with structure: {str_pick_choice: [StateNode]},
        # pick_choice_combo_dict with structure: {str_pick_choice: [(hero_1, hero_2)]}
        if depth == 0:
            t_iter = tqdm(output_next_nodes_dict.items())
        else:
            t_iter = output_next_nodes_dict.items()
        for str_pick_choice, next_node_lst in t_iter:
            # structure [((hero_1, hero_2), value)]
            suggested_hero_list = []

            if depth == 0:
                local_manager = Manager()
                suggested_hero_list = local_manager.list()
                next_node_values_list = local_manager.list()
                mapargs = [(next_node, local_node_ind, depth, alpha, beta, cache_dict,
                            suggested_hero_list, next_node_values_list,
                            pick_choice_combo_dict, str_pick_choice) for local_node_ind, next_node in enumerate(next_node_lst)]
                # process_map(support_map_func, mapargs,
                #             max_workers=10, chunksize=100)
                
                with Pool(10) as pool:
                    try:
                        pool.map(support_map_func, mapargs, chunksize=100)
                    except BetaCutOffException:
                        pool.terminate()
                    pool.join()
                
                max_next_node_value = max(next_node_values_list)
                value = max(value, max_next_node_value)

                suggested_hero_list = list(suggested_hero_list)
                
                # beta pruning inside map 
                alpha = max(alpha, value)

            else:
                for local_node_ind, next_node in enumerate(next_node_lst):
                    next_node_value, _ = alphabeta(
                        next_node, depth + 1, alpha, beta, False, cache_dict)
                    value = max(value, next_node_value)
                    suggested_hero_list_ele = (
                        pick_choice_combo_dict[str_pick_choice][local_node_ind], next_node_value)
                    suggested_hero_list.append(suggested_hero_list_ele)
                    if value > beta:
                        break_flag = True
                        break
                    alpha = max(alpha, value)

            # sort suggested_hero_list
            suggested_hero_list = sorted(
                suggested_hero_list, key=lambda x: x[1], reverse=True)
            suggested_hero_list = suggested_hero_list[:SUGGESTION_NUM]
            suggested_hero_pick_dict[str_pick_choice] = suggested_hero_list
            if break_flag:
                break

        cache_dict[str(node)] = (value, suggested_hero_pick_dict)

        return value, suggested_hero_pick_dict

    else:
        value = 9999
        break_flag = False
        for str_pick_choice, next_node_lst in output_next_nodes_dict.items():
            for next_node in next_node_lst:
                next_node_value, _ = alphabeta(
                    next_node, depth + 1, alpha, beta, True, cache_dict)
                value = min(value, next_node_value)
                if value < alpha:
                    break_flag = True
                    break
                beta = min(beta, value)
            if break_flag:
                break
        return value, None


if __name__ == "__main__":
    # debug
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)

    record_folder = os.path.join(os.path.dirname(__file__), "../data/records")
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

    versus_winrate_matrix_fp = os.path.join(
        record_folder, "versus_winrate_matrix.pkl")
    with_winrate_matrix_fp = os.path.join(
        record_folder, "with_winrate_matrix.pkl")
    counter_rate_matrix_fp = os.path.join(
        record_folder, "counter_rate_matrix.pkl")

    with open(versus_winrate_matrix_fp, 'rb') as f:
        versus_winrate_matrix = pickle.load(f)

    with open(with_winrate_matrix_fp, 'rb') as f:
        with_winrate_matrix = pickle.load(f)

    with open(counter_rate_matrix_fp, 'rb') as f:
        counter_rate_matrix = pickle.load(f)

    manager = Manager()
    alpha_beta_cache_dict = manager.dict()
    # round 5
    # start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5)\
    #     .add_hero("Huskar", False, 1).add_hero("Spectre", False, 2)\
    #     .add_hero("Arc Warden", True, 3).add_hero("Bristleback", True, 4)\
    #     .add_hero("Tiny", False, 3).add_hero("Axe", False, 4)

    # round 3
    start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5)\
        .add_hero("Huskar", False, 1).add_hero("Spectre", False, 2)
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, alpha_beta_cache_dict)
    # save cache
    print("Save dict ing...")
    with open(os.path.join(record_folder, f"depth_limit_{DEPTH_LIMIT}_alpha_beta_cache_dict.pkl"), 'wb') as f:
        pickle.dump(dict(alpha_beta_cache_dict), f)
    print("Second time with cache")
    print(f"A Cache size {len(alpha_beta_cache_dict)}")

    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, alpha_beta_cache_dict)

    # Eval records
    # DEPTH_LIMIT = 1 Round 3 Time: 04:35
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache Time: 04:27
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache Time: 01:17 still slow
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache but using multiprocessing.Pool Time: 02:42 So Dont use it

    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache with Full Depth save Time: 00:00
