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
import time

from natsort import natsorted
from config import ACTIVATE_SAVING_CACHE, DEPTH_LIMIT, PRUNE_WORST_HERO_NUM, SUGGESTION_NUM
from pickaction import StateNode
from heuristic import calculate_heuristic
from tqdm.auto import tqdm
from multiprocessing import Manager, Pool
from tqdm.contrib.concurrent import process_map, thread_map
from multiprocessing import Pool, Process, Manager, Lock
import threading
import queue
from multiprocessing.pool import ThreadPool


# this file implements the alpha beta pruning method

# need a function to detect whether need to run alpha beta

# ! global variable
record_folder = os.path.join(os.path.dirname(__file__), "data/records")

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


class ABCutOffException(Exception):
    pass


def support_thread_map_func_minimize(args):

    next_node, depth, alpha, beta_queue, depth_limit, cache_dict, next_node_values_list, break_flag_list, activate_saving_cache = args
    beta = beta_queue.get()
    next_node_value, _ = alphabeta(
        next_node, depth + 1, alpha, beta, True, depth_limit, cache_dict, activate_saving_cache)
    next_node_values_list.append(next_node_value)

    if next_node_value < alpha:
        beta_queue.put(beta)  # inform main thread
        break_flag_list.append(1)
        raise ABCutOffException
    beta = min(beta, next_node_value)
    beta_queue.put(beta)


def support_thread_map_func_maximize(args):
    next_node, local_node_ind, depth, alpha_queue, beta, depth_limit, cache_dict, suggested_hero_list, next_node_values_list, pick_choice_combo_dict, str_pick_choice, break_flag_list, activate_saving_cache = args
    alpha = alpha_queue.get()
    next_node_value, _ = alphabeta(
        next_node, depth + 1, alpha, beta, False, depth_limit, cache_dict, activate_saving_cache)
    next_node_values_list.append(next_node_value)
    suggested_hero_list.append(
        (pick_choice_combo_dict[str_pick_choice][local_node_ind], next_node_value))

    if next_node_value > beta:
        alpha_queue.put(alpha)  # inform main thread
        break_flag_list.append(1)
        raise ABCutOffException
    alpha = max(alpha, next_node_value)
    alpha_queue.put(alpha)


def support_process_map_func(args):
    # ! need manager
    next_node, local_node_ind, depth, alpha_m, beta, depth_limit, cache_dict, suggested_hero_list, next_node_values_list, pick_choice_combo_dict, str_pick_choice, break_flag_list, activate_saving_cache = args
    next_node_value, _ = alphabeta(
        next_node, depth + 1, alpha_m.value, beta, False, depth_limit, cache_dict, activate_saving_cache)
    next_node_values_list.append(next_node_value)
    suggested_hero_list.append(
        (pick_choice_combo_dict[str_pick_choice][local_node_ind], next_node_value))

    if next_node_value > beta:
        break_flag_list.append(1)
        raise ABCutOffException

    alpha_m.value = max(alpha_m.value, next_node_value)


def alphabeta(node: StateNode, depth, alpha, beta, is_maximizing_player, depth_limit, cache_dict = None, activate_saving_cache=ACTIVATE_SAVING_CACHE):
    # if node.cur_round != 0 do not use the warmup dict because we have ban heros and it will affect score
    if cache_dict is not None and node.cur_round == 0 and str(node) in cache_dict:
        if node.cur_round == 0 and depth == 0 and len(node.ban_lst) > 0:
            # ! consider ban hero counter if cur round = 0
            # suggested_hero_list structure = [[(hero_1, hero_2), val]]
            value, suggested_hero_pick_dict = cache_dict[str(node)]
            for str_pick_choice in suggested_hero_pick_dict:
                suggested_hero_list = suggested_hero_pick_dict[str_pick_choice]
                updated_suggested_hero_list = []
                for s_h_l_ind in range(len(suggested_hero_list)):
                    hero_combo, val = suggested_hero_list[s_h_l_ind]
                    h1, h2 = hero_combo
                    if h1 in node.ban_lst or h2 in node.ban_lst:
                        continue
                    countered_most_hero_list = set()
                    for ban_hero in node.ban_lst:
                        # get counter most top PRUNE_WORST_HERO_NUM
                        for tind, ct_hero in enumerate(counter_rate_matrix[ban_hero].keys()):
                            if tind < PRUNE_WORST_HERO_NUM:
                                countered_most_hero_list.add(ct_hero)
                            else:
                                break
                    for hero in hero_combo:
                        if hero in countered_most_hero_list:
                            val += 0.03
                    
                        
                    updated_suggested_hero_list.append([hero_combo, val])
                # sort it again
                updated_suggested_hero_list = sorted(
                    updated_suggested_hero_list, key=lambda x: x[1], reverse=True)
                suggested_hero_pick_dict[str_pick_choice] = updated_suggested_hero_list
            return value, suggested_hero_pick_dict
            # ! -----------------------
        else:
            return cache_dict[str(node)]

    if depth > depth_limit or node.is_terminated():
        value = calculate_heuristic(
            node, counter_rate_matrix, with_winrate_matrix)
        if cache_dict is not None and activate_saving_cache:
            cache_dict[str(node)] = (value, None)
        return value, None

    output_next_nodes_dict, pick_choice_combo_dict = node.next_possible_nodes()
    a = 1
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
                break_flag_list = local_manager.list()
                alpha_m = local_manager.Value('d', alpha)
                mapargs = [(next_node, local_node_ind, depth, alpha_m, beta, depth_limit, cache_dict,
                            suggested_hero_list, next_node_values_list,
                            pick_choice_combo_dict, str_pick_choice, break_flag_list, activate_saving_cache) for local_node_ind, next_node in enumerate(next_node_lst)]

                try:
                    workers_num = 16
                    process_map(support_process_map_func, mapargs,
                                max_workers=workers_num, chunksize=20, leave=False)
                except ABCutOffException:
                    pass
                
                # with Pool(16) as pool:
                #     try:
                #         pool.map(support_process_map_func, mapargs,
                #                     chunksize=20)
                #     except ABCutOffException:
                #         pass

                max_next_node_value = max(next_node_values_list)
                value = max(value, max_next_node_value)

                suggested_hero_list = list(suggested_hero_list)

                alpha = alpha_m.value
                # beta pruning inside map
                # alpha update inside map
                if len(break_flag_list) > 0:
                    break_flag = True

            else:

                # ----- thread pool version -----
                # threading map for depth > 0
                suggested_hero_list = list()
                next_node_values_list = list()
                break_flag_list = list()
                alpha_queue = queue.Queue()
                alpha_queue.put(alpha)

                mapargs = [(next_node, local_node_ind, depth, alpha_queue, beta, depth_limit, cache_dict,
                            suggested_hero_list, next_node_values_list,
                            pick_choice_combo_dict, str_pick_choice, break_flag_list, activate_saving_cache) for local_node_ind, next_node in enumerate(next_node_lst)]
                with ThreadPool(2) as pool:
                    try:
                        pool.map(support_thread_map_func_maximize, mapargs,
                                 chunksize=20)
                    except ABCutOffException:
                        pass
                    
                max_next_node_value = max(next_node_values_list)
                value = max(value, max_next_node_value)

                suggested_hero_list = suggested_hero_list
                alpha = alpha_queue.get(timeout=5)

                # beta pruning inside map
                # alpha update inside map
                if len(break_flag_list) > 0:
                    break_flag = True
                # --------------------------

                # # ------ vanilla loop version -----

                # for local_node_ind, next_node in enumerate(next_node_lst):
                #     next_node_value, _ = alphabeta(
                #         next_node, depth + 1, alpha, beta, False, depth_limit, cache_dict)
                #     value = max(value, next_node_value)
                #     suggested_hero_list_ele = (
                #         pick_choice_combo_dict[str_pick_choice][local_node_ind], next_node_value)
                #     suggested_hero_list.append(suggested_hero_list_ele)
                #     if value > beta:
                #         break_flag = True
                #         break
                #     alpha = max(alpha, value)
                # # ----------------------------

            # sort suggested_hero_list
            suggested_hero_list = sorted(
                suggested_hero_list, key=lambda x: x[1], reverse=True)
            suggested_hero_list = suggested_hero_list[:SUGGESTION_NUM]
            suggested_hero_pick_dict[str_pick_choice] = suggested_hero_list
            if break_flag:
                break
        if cache_dict is not None and activate_saving_cache:
            cache_dict[str(node)] = (value, suggested_hero_pick_dict)

        return value, suggested_hero_pick_dict

    else:
        value = 9999
        break_flag = False
        for str_pick_choice, next_node_lst in output_next_nodes_dict.items():

            # # ------- vanilla loop version -----

            # for next_node in next_node_lst:
            #     next_node_value, _ = alphabeta(
            #         next_node, depth + 1, alpha, beta, True, depth_limit, cache_dict)
            #     value = min(value, next_node_value)
            #     if value < alpha:
            #         break_flag = True
            #         break
            #     beta = min(beta, value)
            # # ------- ---------- -----

            # --------- thread pool version, actually no difference between vanilla though-------
            next_node_values_list = list()
            break_flag_list = list()
            beta_queue = queue.Queue()
            beta_queue.put(beta)

            mapargs = [(next_node, depth, alpha, beta_queue, depth_limit, cache_dict,
                        next_node_values_list,
                        break_flag_list, activate_saving_cache) for next_node in next_node_lst]

            with ThreadPool(2) as pool:
                try:
                    pool.map(support_thread_map_func_minimize, mapargs,
                             chunksize=int(len(mapargs) / 2))
                except ABCutOffException:
                    pass
            min_next_node_value = min(next_node_values_list)
            value = min(value, min_next_node_value)

            beta = beta_queue.get(timeout=5)

            # beta pruning inside map
            # alpha update inside map
            if len(break_flag_list) > 0:
                break_flag = True
            # -----------------------

            if break_flag:
                break
        if cache_dict is not None and activate_saving_cache:
            cache_dict[str(node)] = (value, None)
        return value, None


if __name__ == "__main__":
    # debug
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)
    
    depth_limit = 1


    record_folder = os.path.join(os.path.dirname(__file__), "data/records")
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
    manager = Manager()

    versus_winrate_matrix_fp = os.path.join(
        record_folder, "versus_winrate_matrix.pkl")
    with_winrate_matrix_fp = os.path.join(
        record_folder, "with_winrate_matrix.pkl")
    counter_rate_matrix_fp = os.path.join(
        record_folder, "counter_rate_matrix.pkl")

    warmup_cache_dict_fp = os.path.join(
        record_folder, f"depth_limit_{depth_limit}_warmup_cache_dict.pkl")

    with open(versus_winrate_matrix_fp, 'rb') as f:
        versus_winrate_matrix = pickle.load(f)

    with open(with_winrate_matrix_fp, 'rb') as f:
        with_winrate_matrix = pickle.load(f)

    with open(counter_rate_matrix_fp, 'rb') as f:
        counter_rate_matrix = pickle.load(f)

    with open(warmup_cache_dict_fp, 'rb') as f:
        warmup_cache_dict = pickle.load(f)
    alpha_beta_cache_dict = manager.dict(warmup_cache_dict)
    
    
    # round 5
    # start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5)\
    #     .add_hero("Huskar", False, 1).add_hero("Spectre", False, 2)\
    #     .add_hero("Arc Warden", True, 3).add_hero("Bristleback", True, 4)\
    #     .add_hero("Tiny", False, 3).add_hero("Axe", False, 4)

    # # round 3
    start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5)\
        .add_hero("Huskar", False, 1).add_hero("Spectre", False, 2)
        
    # # round 3 conflict situation
    # start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5)\
    #     .add_hero("Huskar", False, 1).add_hero("Spectre", False, 2)\
    #     .add_hero("Arc Warden", True, 3).add_hero("Bristleback", True, 4).ban_hero("Bristleback")

    # # round 1 conflict situation
    # start_node = StateNode(*ally_hero_pools, *opponent_hero_pools)
    # start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5).ban_hero("Anti-Mage")

    print("With cache")
    print(f"A Cache size {len(alpha_beta_cache_dict)}")

    # print("without cache dict")
    start_time = time.time()
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, depth_limit, alpha_beta_cache_dict)
    
    print(suggested_hero_pick_dict)
    end_time = time.time()
    elapsed_time = end_time - start_time  # in second
    print("Elapsed time in seconds: ", elapsed_time)

    # print("test ban hero")
    # start_node.ban_hero("Muerta")
    # start_time = time.time()
    # value, suggested_hero_pick_dict = alphabeta(
    #     start_node, 0, -999, 999, True, depth_limit, None)
    
    # print(suggested_hero_pick_dict)
    # end_time = time.time()
    # elapsed_time = end_time - start_time  # in second
    # print("Elapsed time in seconds: ", elapsed_time)
    
    # print("with cache dict")
    # start_time = time.time()
    # value, suggested_hero_pick_dict = alphabeta(
    #     start_node, 0, -999, 999, True, depth_limit, alpha_beta_cache_dict)
    
    # print(suggested_hero_pick_dict)
    # end_time = time.time()
    # elapsed_time = end_time - start_time  # in second
    # print("Elapsed time in seconds: ", elapsed_time)
    
    # ! do not add cache dict when predict from round 3 
    # start_node.add_hero("Abaddon", True, 1).add_hero("Anti-Mage", True, 5).ban_hero("Anti-Mage")
    
    # Eval records
    # DEPTH_LIMIT = 1 Round 3 Time: 04:35
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache Time: 04:27
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache Time: 01:17 still slow
    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache but using multiprocessing.Pool Time: 02:42 So Dont use it

    # DEPTH_LIMIT = 1 Round 3 With Heuristic Cache and Alphabeta pruning Cache with Full Depth save Time: 00:00
    # A Cache size 1068238 with local sort. time 01:18
    # without local sort A Cache size 1769087. time 01:33
    
    # DEPTH_LIMIT = 1 Round 3 with prune round 3, 4 by with rate matrix , with sort save Time: 00:50
    # DEPTH_LIMIT = 1 Round 3 with prune round 3, 4 by with rate matrix , without sort save Time: 00:48
    # DEPTH_LIMIT = 1 Round 3 without prune round 3, 4 by with rate matrix , without sort save Time: 00:56
    
    # ! DEPTH_LIMIT = 1 Round 3 empty dict only take 5 sec, meaning that we do not use dict starting from round 3
