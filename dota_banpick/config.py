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

NODE_EXPANSION_LIMIT = 9999
DEPTH_LIMIT = 999

FIRST_ROUND_PICK_CHOICE = [ # need to be in ascending order
    [4, 5],
    [3, 4],
    [3, 5]
]
DEFAULT_COUNTER_TEMPERATURE = 0.8
COUNTER_WEIGHT = 1.0 # increase if we want to focus more on countering the opponents rather than hero combo
POS_1_COUNTER_TEMPERATURE = [1.1,
                             DEFAULT_COUNTER_TEMPERATURE,
                             1.2,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE
                             ]

POS_2_COUNTER_TEMPERATURE = [DEFAULT_COUNTER_TEMPERATURE,
                             1.2,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE
                             ]

POS_3_COUNTER_TEMPERATURE = [1.3,
                             1.0,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE
                             ]

POS_4_COUNTER_TEMPERATURE = [1.2,
                             1.2,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE
                             ]

POS_5_COUNTER_TEMPERATURE = [DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE,
                             1.4,
                             DEFAULT_COUNTER_TEMPERATURE,
                             DEFAULT_COUNTER_TEMPERATURE
                             ]