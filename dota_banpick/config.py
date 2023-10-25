'''
File Created: Tuesday, 17th October 2023 1:51:49 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Tuesday, 17th October 2023 2:11:13 pm
Modified By: Sukai Huang (huangsukai1997@gmail.com>)
-----
Copyright 2023 - 2023 by Sukai@Community Project
All rights reserved.
This file is part of The DOTA 2 BanPick Tool Project,
and is released under The MIT License. Please see the LICENSE
file that should have been included as part of this project.
'''

from glob import glob
import os
import pickle

from natsort import natsorted


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
    
hero_pool_fps = glob(os.path.join(
    record_folder, "default_pos_*_hero_pool.txt"))
hero_pool_fps = natsorted(hero_pool_fps)
default_hero_pools = []
for hp_fp in hero_pool_fps:
    with open(hp_fp, 'r') as f:
        hp_text = f.read()
        default_hero_pools.append(eval(hp_text))

# lane rate info 
lane_rate_dict_fp = os.path.join(
    record_folder, "lane_rate_info_dict.pkl")
with open(lane_rate_dict_fp, 'rb') as f:
    lane_rate_info_dict = pickle.load(f)

LAST_UPDATE = "21 Oct 2023"

COUNTER_WEIGHT = 1.2 # increase if we want to focus more on countering the opponents rather than hero combo
                     # try 0.1 interval 

BAN_SUGGEST_FRONT_POS_COUTNER_WEIGHT = 1.225  

NODE_EXPANSION_LIMIT = 9999
DEPTH_LIMIT = 0 # you cannot have it more than 2,, for real time speed up, set it to 0, 1 would take 10 secs, st to to warmup 
SUGGESTION_NUM = 200

FIRST_ROUND_PICK_CHOICE = [ # need to be in ascending order
    [3, 4],
    [4, 5],
    [3, 5]
]

FIRST_ROUND_COUNTER_CHOICE = [ 
    [1, 2],
    [2, 3],
    [1, 3]
]
PRUNE_WORST_HERO_NUM = 5
ACTIVATE_SAVING_CACHE = False

DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE = 0.8
POS_1_COUNTER_TEMPERATURE = [1.1,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             1.2,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE
                             ]

POS_2_COUNTER_TEMPERATURE = [DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             1.2,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE
                             ]

POS_3_COUNTER_TEMPERATURE = [1.3,
                             1.0,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE
                             ]

POS_4_COUNTER_TEMPERATURE = [1.2,
                             1.2,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE
                             ]

POS_5_COUNTER_TEMPERATURE = [DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             1.4,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE,
                             DEFAULT_PICK_SUGGEST_COUNTER_TEMPERATURE
                             ]

COUNTER_TEMPERATURE_LIST = [
    POS_1_COUNTER_TEMPERATURE,
    POS_2_COUNTER_TEMPERATURE,
    POS_3_COUNTER_TEMPERATURE,
    POS_4_COUNTER_TEMPERATURE,
    POS_5_COUNTER_TEMPERATURE
]