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
import pandas as pd
from natsort import natsorted

OPPONENT_TEAM = 'falcons'
record_folder = os.path.join(os.path.dirname(__file__), "data/records")

opponent_team_hero_score_fp = os.path.join(
    record_folder, f"teams/{OPPONENT_TEAM}/team_hero_score.csv")
opponent_team_hero_score_df = pd.read_csv(opponent_team_hero_score_fp, header=None)
opponent_team_hero_score_df.columns = ['Hero', 'Score']

versus_winrate_matrix_fp = os.path.join(
    record_folder, "versus_winrate_matrix.pkl")
with_winrate_matrix_fp = os.path.join(
    record_folder, "with_winrate_matrix.pkl")
counter_rate_matrix_fp = os.path.join(
    record_folder, "counter_rate_matrix.pkl")
synergy_rate_matrix_fp = os.path.join(
    record_folder, "synergy_rate_matrix.pkl")

with open(versus_winrate_matrix_fp, 'rb') as f:
    versus_winrate_matrix = pickle.load(f)
with open(with_winrate_matrix_fp, 'rb') as f:
    with_winrate_matrix = pickle.load(f)
with open(counter_rate_matrix_fp, 'rb') as f:
    counter_rate_matrix = pickle.load(f)
with open(synergy_rate_matrix_fp, 'rb') as f:
    synergy_rate_matrix = pickle.load(f)
    
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
    record_folder, "lane_rate_info_dict.pkl") # TODO lane rate info 可以根据对手战队习惯进行调整
with open(lane_rate_dict_fp, 'rb') as f:
    lane_rate_info_dict = pickle.load(f)

# lane_rate_info_dict data structure
#  'Muerta': {'url': 'https://stratz.com/heroes/138',
#   'Pos 1 Pick Rate': 0.47728516694033934,
#   'Pos 2 Pick Rate': 0.2008073344280241,
#   'Pos 3 Pick Rate': 0.03908958219303047,
#   'Pos 4 Pick Rate': 0.18757982120051087,
#   'Pos 5 Pick Rate': 0.09523809523809523},
#  'Kez': {'url': 'https://stratz.com/heroes/145',
#   'Pos 1 Pick Rate': 0.4333632525514444,
#   'Pos 2 Pick Rate': 0.4463614906419334,
#   'Pos 3 Pick Rate': 0.07961836375120508,
#   'Pos 4 Pick Rate': 0.022672118613078024,
#   'Pos 5 Pick Rate': 0.017984774442339018}}

ACTIVATE_SAVING_CACHE = True
DEPTH_LIMIT_CAPTAIN = 1 # captain mode, we can go deeper because we have more time to think


with open(os.path.join(os.path.dirname(__file__), "update_time.txt"), 'r') as f:
    LAST_UPDATE = f.read()

COUNTER_WEIGHT = 1.2 # increase if we want to focus more on countering the opponents rather than hero combo
                     # try 0.1 interval 

BAN_IMPACT_TO_ALPHABETA_HEURISTIC = 0.1 # increase if we want to focus more on banning the heroes that impact the alphabeta heuristic the most

BAN_SUGGEST_FRONT_POS_COUTNER_WEIGHT = 1.225  

COUNTER_MOST_BONUS = 0.03 # bonus for countering the most picked hero in the opponent team

NODE_EXPANSION_LIMIT = 9999
DEPTH_LIMIT = 0 # you cannot have it more than 2,, for real time speed up, set it to 0, 1 would take 10 secs, st to to warmup 

SUGGESTION_NUM = 200

ALLY_FIRST_ROUND_PICK_CHOICE = [ # need to be in ascending order # TODO can fit to team preference
    [3, 4],
    [4, 5],
    [3, 5]
]

OPPO_FIRST_ROUND_PICK_CHOICE = [ # need to prevent from picking top meta heroes # TODO can fit to team preference
    [1, 2],
    [2, 3],
    [1, 3]
]

EARLY_STAGE_NOT_CONSIDER_BAN_COMBO = [(1,4), (3,5), (4,5), (1,2)]


PRUNE_WORST_HERO_NUM = 5

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

UNCOMMON_HEROES = ["Meepo", "Visage", "Chen", "Arc Warden", "Lycan", "Broodmother"]

CAPTAIN_BP_ORDER = [
    '1 A B',
    '2 B B',
    '3 B B', 
    '4 A B',
    '5 B B',
    '6 B B',
    '7 A B',
    '8 A P',
    '9 B P',
    '10 A B',
    '11 A B',
    '12 B B',
    '13 B P',
    '14 A P',
    '15 A P',
    '16 B P',
    '17 B P',
    '18 A P',
    '19 A B',
    '20 B B',
    '21 B B',
    '22 A B',
    '23 A P',
    '24 B P',
]

