'''
File Created: Wednesday, 18th October 2023 4:36:27 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Wednesday, 18th October 2023 4:36:36 pm
Modified By: Sukai Huang (huangsukai1997@gmail.com>)
-----
Copyright 2023 - 2023 by Sukai@Community Project
All rights reserved.
This file is part of The DOTA 2 BanPick Tool Project,
and is released under The MIT License. Please see the LICENSE
file that should have been included as part of this project.
'''

# alphe beta pruning method is expensive, thus we need to get cache to speed up 

from glob import glob
import logging
from multiprocessing import Manager
import os
import pickle

from natsort import natsorted
from alphabeta import alphabeta
from config import DEPTH_LIMIT
import time
from tqdm.auto import tqdm

from pickaction import StateNode

def generate_warmup_cache():
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

    manager = Manager()
    alpha_beta_cache_dict = manager.dict()
    depth_limit = 2 # ! preprocessing with big number
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, depth_limit, alpha_beta_cache_dict)
    # save cache
    print("Save dict ing...")
    with open(os.path.join(record_folder, f"depth_limit_{depth_limit}_warmup_cache_dict.pkl"), 'wb') as f:
        pickle.dump(dict(alpha_beta_cache_dict), f)
    print("test time with cache")
    print(f"A Cache size {len(alpha_beta_cache_dict)}")
    start_time = time.time()
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, depth_limit,alpha_beta_cache_dict)
    
    end_time = time.time()
    elapsed_time = end_time - start_time # in second
    print("Elapsed time in seconds: ", elapsed_time) 
    
def pre_sort_counter_rate_matrix():
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)
    record_folder = os.path.join(os.path.dirname(__file__), "../data/records")


    counter_rate_matrix_fp = os.path.join(
        record_folder, "counter_rate_matrix.pkl")


    with open(counter_rate_matrix_fp, 'rb') as f:
        counter_rate_matrix = pickle.load(f)
        
    sorted_counter_rate_matrix = dict()
    for hero_name in tqdm(counter_rate_matrix):
        cr_dict = counter_rate_matrix[hero_name]
        sorted_cr_dict_list = sorted(cr_dict.items(), key=lambda x:x[1], reverse=True)
        sorted_cr_dict = dict()
        for k, v in sorted_cr_dict_list:
            sorted_cr_dict[k] = v
        sorted_counter_rate_matrix[hero_name] = sorted_cr_dict
        
    # save it 
    with open(counter_rate_matrix_fp, 'wb') as f:
        pickle.dump(sorted_counter_rate_matrix, f)

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

    manager = Manager()
    alpha_beta_cache_dict = manager.dict()
    depth_limit = 2 # ! preprocessing with big number
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, depth_limit, alpha_beta_cache_dict)
    # save cache
    print("Save dict ing...")
    with open(os.path.join(record_folder, f"depth_limit_{depth_limit}_warmup_cache_dict.pkl"), 'wb') as f:
        pickle.dump(dict(alpha_beta_cache_dict), f)
    print("test time with cache")
    print(f"A Cache size {len(alpha_beta_cache_dict)}")
    start_time = time.time()
    value, suggested_hero_pick_dict = alphabeta(
        start_node, 0, -999, 999, True, depth_limit,alpha_beta_cache_dict)
    
    end_time = time.time()
    elapsed_time = end_time - start_time # in second
    print("Elapsed time in seconds: ", elapsed_time) 