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

from config import *


def calculate_heuristic(statenode,
                        counter_weight = COUNTER_WEIGHT,
                        pos_1_counter_temperature = POS_1_COUNTER_TEMPERATURE,
                        pos_2_counter_temperature = POS_2_COUNTER_TEMPERATURE,
                        pos_3_counter_temperature = POS_3_COUNTER_TEMPERATURE,
                        pos_4_counter_temperature = POS_4_COUNTER_TEMPERATURE,
                        pos_5_counter_temperature = POS_5_COUNTER_TEMPERATURE,

                        ):
    """it will return the advantage value for your team. 
    Your team's goal is to maximise it, while the opponent team's goal is to minimise it

    Return: 
        numeric score
    """
    
    
def compute_bad_picks_for_each_pos(statenode,
                        counter_weight = COUNTER_WEIGHT,
                        pos_1_counter_temperature = POS_1_COUNTER_TEMPERATURE,
                        pos_2_counter_temperature = POS_2_COUNTER_TEMPERATURE,
                        pos_3_counter_temperature = POS_3_COUNTER_TEMPERATURE,
                        pos_4_counter_temperature = POS_4_COUNTER_TEMPERATURE,
                        pos_5_counter_temperature = POS_5_COUNTER_TEMPERATURE,

                        ):
    # output structure : list[{pos: [bad_hero_ele,]}]
    pass