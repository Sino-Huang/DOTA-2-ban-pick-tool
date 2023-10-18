'''
File Created: Tuesday, 17th October 2023 1:51:17 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Tuesday, 17th October 2023 2:12:33 pm
Modified By: Sukai Huang (huangsukai1997@gmail.com>)
-----
Copyright 2023 - 2023 by Sukai@Community Project
All rights reserved.
This file is part of The DOTA 2 BanPick Tool Project,
and is released under The MIT License. Please see the LICENSE
file that should have been included as part of this project.
'''

# this file implements what can be the next possible actions so as to expand the search nodes
import logging
import copy
import itertools
import os
import random
from natsort import natsorted
from glob import glob
import pickle

import numpy as np
from config import FIRST_ROUND_PICK_CHOICE
from config import PRUNE_WORST_HERO_NUM

record_folder = os.path.join(os.path.dirname(__file__), "../data/records")


with_winrate_matrix_fp = os.path.join(
    record_folder, "with_winrate_matrix.pkl")
counter_rate_matrix_fp = os.path.join(
    record_folder, "counter_rate_matrix.pkl")

with open(with_winrate_matrix_fp, 'rb') as f:
    with_winrate_matrix = pickle.load(f)

with open(counter_rate_matrix_fp, 'rb') as f:
    counter_rate_matrix = pickle.load(f)


class StateNode:
    """it will store picked and baned heros and round count
    """

    def __init__(self,
                 ally_pos_1_hero_pool,
                 ally_pos_2_hero_pool,
                 ally_pos_3_hero_pool,
                 ally_pos_4_hero_pool,
                 ally_pos_5_hero_pool,
                 opponent_pos_1_hero_pool,
                 opponent_pos_2_hero_pool,
                 opponent_pos_3_hero_pool,
                 opponent_pos_4_hero_pool,
                 opponent_pos_5_hero_pool,
                 ) -> None:

        # static var
        self.ally_pos_1_hero_pool = ally_pos_1_hero_pool
        self.ally_pos_2_hero_pool = ally_pos_2_hero_pool
        self.ally_pos_3_hero_pool = ally_pos_3_hero_pool
        self.ally_pos_4_hero_pool = ally_pos_4_hero_pool
        self.ally_pos_5_hero_pool = ally_pos_5_hero_pool
        self.opponent_pos_1_hero_pool = opponent_pos_1_hero_pool
        self.opponent_pos_2_hero_pool = opponent_pos_2_hero_pool
        self.opponent_pos_3_hero_pool = opponent_pos_3_hero_pool
        self.opponent_pos_4_hero_pool = opponent_pos_4_hero_pool
        self.opponent_pos_5_hero_pool = opponent_pos_5_hero_pool

        # dynamic var
        self.ally_pos_1_pick_round = 0
        self.ally_pos_2_pick_round = 0
        self.ally_pos_3_pick_round = 0
        self.ally_pos_4_pick_round = 0
        self.ally_pos_5_pick_round = 0
        self.opponent_pos_1_pick_round = 0
        self.opponent_pos_2_pick_round = 0
        self.opponent_pos_3_pick_round = 0
        self.opponent_pos_4_pick_round = 0
        self.opponent_pos_5_pick_round = 0

        self.ally_pos_1_hero = None
        self.ally_pos_2_hero = None
        self.ally_pos_3_hero = None
        self.ally_pos_4_hero = None
        self.ally_pos_5_hero = None
        self.opponent_pos_1_hero = None
        self.opponent_pos_2_hero = None
        self.opponent_pos_3_hero = None
        self.opponent_pos_4_hero = None
        self.opponent_pos_5_hero = None

        # 1 means 1st round pick, in ALL pick mode, 1: ally 2 heros, 2: opponent 2 heros,
        self.cur_round = 0
        # 3: ally 2 heros, 4: opponent 2 heros
        # 5: ally 1 hero , 6: opponent 1 hero
        # dynamic ban list
        # ban list also contains the picked up heros (so it is more suitable to call it unavailabe hero list)
        self.ban_lst = []
        # -- end dynamic var --

    def __copy__(self):
        new_node = StateNode(self.ally_pos_1_hero_pool,
                             self.ally_pos_2_hero_pool,
                             self.ally_pos_3_hero_pool,
                             self.ally_pos_4_hero_pool,
                             self.ally_pos_5_hero_pool,
                             self.opponent_pos_1_hero_pool,
                             self.opponent_pos_2_hero_pool,
                             self.opponent_pos_3_hero_pool,
                             self.opponent_pos_4_hero_pool,
                             self.opponent_pos_5_hero_pool)

        # copy all dynamic var
        new_node.ally_pos_1_pick_round = self.ally_pos_1_pick_round
        new_node.ally_pos_2_pick_round = self.ally_pos_2_pick_round
        new_node.ally_pos_3_pick_round = self.ally_pos_3_pick_round
        new_node.ally_pos_4_pick_round = self.ally_pos_4_pick_round
        new_node.ally_pos_5_pick_round = self.ally_pos_5_pick_round
        new_node.opponent_pos_1_pick_round = self.opponent_pos_1_pick_round
        new_node.opponent_pos_2_pick_round = self.opponent_pos_2_pick_round
        new_node.opponent_pos_3_pick_round = self.opponent_pos_3_pick_round
        new_node.opponent_pos_4_pick_round = self.opponent_pos_4_pick_round
        new_node.opponent_pos_5_pick_round = self.opponent_pos_5_pick_round

        new_node.ally_pos_1_hero = self.ally_pos_1_hero
        new_node.ally_pos_2_hero = self.ally_pos_2_hero
        new_node.ally_pos_3_hero = self.ally_pos_3_hero
        new_node.ally_pos_4_hero = self.ally_pos_4_hero
        new_node.ally_pos_5_hero = self.ally_pos_5_hero
        new_node.opponent_pos_1_hero = self.opponent_pos_1_hero
        new_node.opponent_pos_2_hero = self.opponent_pos_2_hero
        new_node.opponent_pos_3_hero = self.opponent_pos_3_hero
        new_node.opponent_pos_4_hero = self.opponent_pos_4_hero
        new_node.opponent_pos_5_hero = self.opponent_pos_5_hero
        new_node.cur_round = self.cur_round
        new_node.ban_lst = copy.deepcopy(self.ban_lst)
        return new_node

    def ban_hero(self, ban_hero_name):
        """we have two cases, one is directly ban heros, the other one is that we have the pick same hero situation

        Args:
            hero_name (str): ban_hero name
        """
        # pick same hero situation
        hero_list = [self.ally_pos_1_hero,
                     self.ally_pos_2_hero,
                     self.ally_pos_3_hero,
                     self.ally_pos_4_hero,
                     self.ally_pos_5_hero]
        hero_pick_round_list = [self.ally_pos_1_pick_round,
                                self.ally_pos_2_pick_round,
                                self.ally_pos_3_pick_round,
                                self.ally_pos_4_pick_round,
                                self.ally_pos_5_pick_round]
        if ban_hero_name in hero_list:
            # check if current pick
            ban_hero_index = hero_list.index(ban_hero_name)
            ban_hero_pick_round = hero_pick_round_list[ban_hero_index]
            if ban_hero_pick_round != self.cur_round:
                logging.warning(
                    "You cannot ban an hero that is already picked")
                return self
            else:
                # pick same hero situation, remove that hero

                if ban_hero_index == 0:
                    self.ally_pos_1_hero = None
                    self.ally_pos_1_pick_round = 0

                elif ban_hero_index == 1:
                    self.ally_pos_2_hero = None
                    self.ally_pos_2_pick_round = 0
                elif ban_hero_index == 2:
                    self.ally_pos_3_hero = None
                    self.ally_pos_3_pick_round = 0
                elif ban_hero_index == 3:
                    self.ally_pos_4_hero = None
                    self.ally_pos_4_pick_round = 0
                elif ban_hero_index == 4:
                    self.ally_pos_5_hero = None
                    self.ally_pos_5_pick_round = 0
                if self.cur_round == 5:  # ! for round 5, if pick same hero, we can treat it like we just finish round 4
                    self.cur_round = 4
                return self
        else:
            # normal ban situation
            if ban_hero_name not in self.ban_lst:
                self.ban_lst.append(ban_hero_name)
            return self

    def _hero_set(self, hero_name, ind, is_ally):
        """this set method will also update pick round
        """
        if ind == 0:
            if is_ally:
                if self.ally_pos_1_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.ally_pos_1_hero = hero_name
                self.ally_pos_1_pick_round = self.cur_round
            else:
                if self.opponent_pos_1_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.opponent_pos_1_hero = hero_name
                self.opponent_pos_1_pick_round = self.cur_round
        elif ind == 1:
            if is_ally:
                if self.ally_pos_2_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.ally_pos_2_hero = hero_name
                self.ally_pos_2_pick_round = self.cur_round
            else:
                if self.opponent_pos_2_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.opponent_pos_2_hero = hero_name
                self.opponent_pos_2_pick_round = self.cur_round
        elif ind == 2:
            if is_ally:
                if self.ally_pos_3_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.ally_pos_3_hero = hero_name
                self.ally_pos_3_pick_round = self.cur_round
            else:
                if self.opponent_pos_3_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.opponent_pos_3_hero = hero_name
                self.opponent_pos_3_pick_round = self.cur_round
        elif ind == 3:
            if is_ally:
                if self.ally_pos_4_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.ally_pos_4_hero = hero_name
                self.ally_pos_4_pick_round = self.cur_round
            else:
                if self.opponent_pos_4_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.opponent_pos_4_hero = hero_name
                self.opponent_pos_4_pick_round = self.cur_round
        elif ind == 4:
            if is_ally:
                if self.ally_pos_5_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.ally_pos_5_hero = hero_name
                self.ally_pos_5_pick_round = self.cur_round
            else:
                if self.opponent_pos_5_hero is not None:
                    logging.warning("has already occupied")
                    return
                self.opponent_pos_5_hero = hero_name
                self.opponent_pos_5_pick_round = self.cur_round
        # add name to ban list
        self.ban_lst.append(hero_name)

    def add_hero(self, hero_name, is_ally, position):
        """add hero to either ally or opponent
        update cur round and ban list and hero info

        Args:
            hero_name (_type_): _description_
            position: the natural dota position 1 - 5
        """
        position_index = position - 1  # pythonic index sorry about that

        ally_hero_pick_round_list = [self.ally_pos_1_pick_round,
                                     self.ally_pos_2_pick_round,
                                     self.ally_pos_3_pick_round,
                                     self.ally_pos_4_pick_round,
                                     self.ally_pos_5_pick_round]

        opponent_hero_pick_round_list = [
            self.opponent_pos_1_pick_round,
            self.opponent_pos_2_pick_round,
            self.opponent_pos_3_pick_round,
            self.opponent_pos_4_pick_round,
            self.opponent_pos_5_pick_round
        ]
        # check is available
        if hero_name in self.ban_lst:
            logging.warning(f"hero {hero_name} is not available already")
            return self

        if is_ally:
            # two sit, one is to progress to new round, the other is to achieve current round
            # check if progress to new round
            if self.cur_round in [0, 2, 4] and opponent_hero_pick_round_list.count(self.cur_round) >= 2:
                self.cur_round += 1
                # ally hero update
                self._hero_set(hero_name, position_index, is_ally)

            # check if achieve current round
            elif self.cur_round in [1, 3] and ally_hero_pick_round_list.count(self.cur_round) == 1:
                # ally hero update
                self._hero_set(hero_name, position_index, is_ally)

            else:
                logging.warning("invalid add ally hero case")

        else:
            # two sit, one is to progress to new round, the other is to achieve current round
            # check if progress to new round
            if self.cur_round in [1, 3] and ally_hero_pick_round_list.count(self.cur_round) == 2:
                self.cur_round += 1
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            # new round case 2
            elif self.cur_round in [5] and ally_hero_pick_round_list.count(self.cur_round) == 1:
                self.cur_round += 1
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            # check if achieve current round
            elif self.cur_round in [2, 4] and opponent_hero_pick_round_list.count(self.cur_round) == 1:
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            else:
                logging.warning("invalid add opponent hero case")

        return self

    def next_possible_nodes(self, first_round_pick_choice=FIRST_ROUND_PICK_CHOICE):
        """generate a list of possible nodes, based on the current round
        remember the first round pos combo restriction

        Returns: output_next_nodes_dict with structure {str_pick_choice: [StateNode]},  
                 pick_choice_combo_dict with structure: {str_pick_choice: [(hero_1, hero_2)]}

        """
        # some properties for next nodes:
        # 1. cur round increase, complete round hero suggestion
        # 2. first 2 rounds pos combo restriction
        # 3. hero pool restricted

        is_ally_next_turn = None
        hero_list = None

        ally_hero_pick_round_list = [self.ally_pos_1_pick_round,
                                     self.ally_pos_2_pick_round,
                                     self.ally_pos_3_pick_round,
                                     self.ally_pos_4_pick_round,
                                     self.ally_pos_5_pick_round]

        # get available hero pools
        if self.cur_round in [0, 2, 4]:
            is_ally_next_turn = True
        elif self.cur_round in [1, 3] and ally_hero_pick_round_list.count(self.cur_round) == 1:
            is_ally_next_turn = True
        else:
            is_ally_next_turn = False

        if is_ally_next_turn:
            # define hero pool
            hero_pool_lst = [
                self.ally_pos_1_hero_pool,
                self.ally_pos_2_hero_pool,
                self.ally_pos_3_hero_pool,
                self.ally_pos_4_hero_pool,
                self.ally_pos_5_hero_pool
            ]

            hero_list = [self.ally_pos_1_hero,
                         self.ally_pos_2_hero,
                         self.ally_pos_3_hero,
                         self.ally_pos_4_hero,
                         self.ally_pos_5_hero]

            paired_hero_list = [
                self.opponent_pos_1_hero,
                self.opponent_pos_2_hero,
                self.opponent_pos_3_hero,
                self.opponent_pos_4_hero,
                self.opponent_pos_5_hero]
            
            paired_hero_list = [x for x in paired_hero_list if x is not None]

        else:
            hero_pool_lst = [
                self.opponent_pos_1_hero_pool,
                self.opponent_pos_2_hero_pool,
                self.opponent_pos_3_hero_pool,
                self.opponent_pos_4_hero_pool,
                self.opponent_pos_5_hero_pool
            ]

            hero_list = [
                self.opponent_pos_1_hero,
                self.opponent_pos_2_hero,
                self.opponent_pos_3_hero,
                self.opponent_pos_4_hero,
                self.opponent_pos_5_hero]

            paired_hero_list = [self.ally_pos_1_hero,
                                self.ally_pos_2_hero,
                                self.ally_pos_3_hero,
                                self.ally_pos_4_hero,
                                self.ally_pos_5_hero]
            
            paired_hero_list = [x for x in paired_hero_list if x is not None]
            

        # ! to speed up, auto remove a number of worst heros
        # paird hero list filter out PRUNE_WORST_HERO_NUM heros
        # PRUNE_WORST_HERO_NUM
        worst_hero_list = set()
        for paired_hero in paired_hero_list:
            for ind, key in enumerate(counter_rate_matrix[paired_hero].keys()):
                if ind < PRUNE_WORST_HERO_NUM:
                    worst_hero_list.add(key)
                else:
                    break


        # filter available hero pools
        filtered_hero_pool_lst = []
        for pool in hero_pool_lst:
            pool_copy = copy.deepcopy(pool)  # type: list
            for unavailable_hero in self.ban_lst:
                if unavailable_hero in pool_copy:
                    pool_copy.remove(unavailable_hero)
            for worst_hero in worst_hero_list:
                if worst_hero in pool_copy:
                    pool_copy.remove(worst_hero)

            filtered_hero_pool_lst.append(pool_copy)

        # check available combo
        # make copy first and then use add hero function in the new instance
        next_round = self.cur_round + 1
        # structure: {pick_choice: [(hero_1, hero_2)]}, later flatten it to have list of nodes
        pick_choice_combo_dict = dict()

        # consider pick same hero situation
        pick_same_hero_sit_flag = False
        if self.cur_round in [1, 3] and ally_hero_pick_round_list.count(self.cur_round) == 1:
            # we set a flag and some mods
            pick_same_hero_sit_flag = True
            # next round is still cur_round though we fix one hero input
            next_round = self.cur_round

            fix_hero_pos_ind = ally_hero_pick_round_list.index(self.cur_round)
            fix_hero = hero_list[fix_hero_pos_ind]
            fix_hero_pos = fix_hero_pos_ind + 1

        # normal case
        if next_round in [1, 2]:
            # you can only pick under restriction
            for pick_choice in first_round_pick_choice:
                if pick_same_hero_sit_flag:
                    if fix_hero_pos not in pick_choice:  # skip choice where we do not have fix hero pos
                        continue
                pc_sorted = pick_choice # ! assume sort arry for first round
                if pick_same_hero_sit_flag:
                    fix_hero_pos_local_ind = pc_sorted.index(fix_hero_pos)
                pick_indexs = [x - 1 for x in pc_sorted]  # pythonic index
                assert len(pick_indexs) == 2
                hero_pool_a = filtered_hero_pool_lst[pick_indexs[0]]
                hero_pool_b = filtered_hero_pool_lst[pick_indexs[1]]

                if pick_same_hero_sit_flag:
                    if fix_hero_pos_local_ind == 0:
                        hero_pool_a = [fix_hero]
                    else:
                        hero_pool_b = [fix_hero]

                hero_pick_combo_list = [
                    (a, b) for a in hero_pool_a for b in hero_pool_b if a != b]
                pick_choice_combo_dict[str(pc_sorted)] = hero_pick_combo_list

        elif next_round in [3, 4]:
            # you need to check what pos combo is available
            available_pos_lst = []  # natural dota position number 1-5
            for ind in range(len(hero_list)):
                if hero_list[ind] is None:
                    available_pos_lst.append(ind + 1)

            available_pos_lst = sorted(available_pos_lst)
            round_pick_choice = list(
                itertools.combinations(available_pos_lst, 2))
            for pick_choice in round_pick_choice:
                if pick_same_hero_sit_flag:
                    if fix_hero_pos not in pick_choice:  # skip choice where we do not have fix hero pos
                        continue
                pc_sorted = pick_choice # ! assume already done after itertools.combination
                if pick_same_hero_sit_flag:
                    fix_hero_pos_local_ind = pc_sorted.index(fix_hero_pos)

                pick_indexs = [x - 1 for x in pc_sorted]  # pythonic index
                assert len(pick_indexs) == 2
                hero_pool_a = filtered_hero_pool_lst[pick_indexs[0]]
                hero_pool_b = filtered_hero_pool_lst[pick_indexs[1]]

                if pick_same_hero_sit_flag:
                    if fix_hero_pos_local_ind == 0:
                        hero_pool_a = [fix_hero]
                    else:
                        hero_pool_b = [fix_hero]

                hero_pick_combo_list = [
                    (a, b) for a in hero_pool_a for b in hero_pool_b if a != b]
                pick_choice_combo_dict[str(pc_sorted)] = hero_pick_combo_list

        else:  # meaning is [5,6]
            # get the last available pos
            # you need to check what pos combo is available
            available_pos_lst = []  # natural dota position number 1-5
            for ind in range(len(hero_list)):
                if hero_list[ind] is None:
                    available_pos_lst.append(ind + 1)

            assert len(available_pos_lst) == 1
            pick_choice = available_pos_lst
            pc_sorted = pick_choice

            pick_indexs = [x - 1 for x in pc_sorted]  # pythonic index
            assert len(pick_indexs) == 1
            hero_pool_a = filtered_hero_pool_lst[pick_indexs[0]]
            hero_pick_combo_list = [(a,) for a in hero_pool_a]
            pick_choice_combo_dict[str(pc_sorted)] = hero_pick_combo_list

        # now we have the pick_choice_combo_dict, flatten it and generate new nodes. also return pick_choice_combo_dict
        # output_next_nodes_dict with structure {str_pick_choice: [StateNode]},
        
        output_next_nodes_dict = dict()
        node_expansion_count = 0
        for str_pos_pick_choice, combo_list in pick_choice_combo_dict.items():
            # ! --sort the pick_choice_combo_dict may help pruning ---
            def measure_counter(combo):
                if len(paired_hero_list) > 0:
                    # random measure 
                    t_ind_hero = random.randint(0,1)
                    t_ind_pair = random.randint(0,len(paired_hero_list)-1)
                    return counter_rate_matrix[combo[t_ind_hero]][paired_hero_list[t_ind_pair]]
                elif len(combo) == 2:
                    return with_winrate_matrix[combo[0]][combo[1]]
                else:
                    return 0.0
            if len(combo_list[0]) == 2:
                combo_list = sorted(combo_list, key=measure_counter, reverse=True)
                pick_choice_combo_dict[str_pos_pick_choice] = combo_list # store back
            # ! -----------------------------------------------------
            
            output_next_nodes_dict[str_pos_pick_choice] = []
            pos_pick_choice = eval(str_pos_pick_choice)  # type: tuple
            for combo in combo_list:  # combo_list is [(hero_a, hero_b)]
                # create new node
                new_node = self.__copy__()
                for ind, pos in enumerate(pos_pick_choice):
                    if pick_same_hero_sit_flag:  # add already if pick same hero sit
                        if pos == fix_hero_pos:
                            continue
                    new_node.add_hero(
                        hero_name=combo[ind], is_ally=is_ally_next_turn, position=pos)
                output_next_nodes_dict[str_pos_pick_choice].append(new_node)
                node_expansion_count += 1
        logging.info(f"node expansion with size {node_expansion_count}")

        return output_next_nodes_dict, pick_choice_combo_dict

    def is_terminated(self):
        if self.ally_pos_1_hero is not None \
                and self.ally_pos_2_hero is not None \
                and self.ally_pos_3_hero is not None \
                and self.ally_pos_4_hero is not None \
                and self.ally_pos_5_hero is not None \
                and self.opponent_pos_1_hero is not None \
                and self.opponent_pos_2_hero is not None \
                and self.opponent_pos_3_hero is not None \
                and self.opponent_pos_4_hero is not None \
                and self.opponent_pos_5_hero is not None:
            return True
        else:
            return False

    def __repr__(self) -> str:
        ally_hero_list = [self.ally_pos_1_hero,
                          self.ally_pos_2_hero,
                          self.ally_pos_3_hero,
                          self.ally_pos_4_hero,
                          self.ally_pos_5_hero]

        opponent_hero_lst = [
            self.opponent_pos_1_hero,
            self.opponent_pos_2_hero,
            self.opponent_pos_3_hero,
            self.opponent_pos_4_hero,
            self.opponent_pos_5_hero
        ]
        output = ""
        output += "Ally:\n"
        for hero in ally_hero_list:
            output += f"\t{hero}\n"
        output += "Oppo:\n"
        for hero in opponent_hero_lst:
            output += f"\t{hero}\n"
        output += f"Current Round: {self.cur_round}\n"
        return output


if __name__ == "__main__":
    # debug
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

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
    output_next_nodes_dict, pick_choice_combo_dict = start_node.next_possible_nodes()

# start_node.add_hero('Axe', True, 3).add_hero('Bane', False, 3)
# start_node.add_hero('Axe', True, 3).add_hero('Bane', True, 4).ban_hero('Bane')
# next_node = output_next_nodes_dict[str([3,5])][5]
# next_node.add_hero("Visage", False, 1).add_hero("Elder Titan", False, 2).add_hero("Abaddon", True, 1)\
#     .add_hero("Anti-Mage", True, 2).add_hero("Arc Warden", False, 3).add_hero("Bristleback", False, 4)
# next_node.add_hero("Broodmother", True, 4)
# next_node.add_hero("Broodmother", True, 4).ban_hero('Broodmother')
# next_node.add_hero("Broodmother", True, 4).ban_hero('Broodmother')
# output_next_nodes_dict, pick_choice_combo_dict = next_node.next_possible_nodes()
# output_next_nodes_dict['[4]']
