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
from config import FIRST_ROUND_PICK_CHOICE, with_winrate_matrix, counter_rate_matrix, lane_rate_info_dict
from config import PRUNE_WORST_HERO_NUM
from scipy.optimize import linear_sum_assignment

def maximum_assignment_heroes(hero_list_full, hero_round_list_full):
    hero_list_full_filtered = [x for x in hero_list_full if x is not None]
    G = []
    for hero in hero_list_full_filtered:
        lang_scores = [
            lane_rate_info_dict[hero]['Pos 1 Pick Rate'],
            lane_rate_info_dict[hero]['Pos 2 Pick Rate'],
            lane_rate_info_dict[hero]['Pos 3 Pick Rate'],
            lane_rate_info_dict[hero]['Pos 4 Pick Rate'],
            lane_rate_info_dict[hero]['Pos 5 Pick Rate'],
        ]
        G.append(lang_scores)
    
    G = np.asarray(G, dtype=np.float32)        
    row_ind, col_ind = linear_sum_assignment(G,maximize=True)
    
    output_round_lst = [0 for _ in range(5)]
    output_hero_lst = [None for _ in range(5)]
    for ind, heroname in enumerate(hero_list_full_filtered):
        hrond = hero_round_list_full[hero_list_full.index(heroname)]
        the_pos = col_ind[ind]
        output_hero_lst[the_pos] = heroname
        output_round_lst[the_pos] = hrond

    return output_hero_lst, output_round_lst


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
        self.ally_hero_pools = [ally_pos_1_hero_pool,
                                ally_pos_2_hero_pool,
                                ally_pos_3_hero_pool,
                                ally_pos_4_hero_pool,
                                ally_pos_5_hero_pool]
        self.opponent_hero_pools = [opponent_pos_1_hero_pool,
                                    opponent_pos_2_hero_pool,
                                    opponent_pos_3_hero_pool,
                                    opponent_pos_4_hero_pool,
                                    opponent_pos_5_hero_pool,]
        # dynamic var
        self.ally_pick_rounds = [0 for _ in range(5)]
        self.opponent_pick_rounds = [0 for _ in range(5)]

        self.ally_heros = [None for _ in range(5)]

        self.opponent_heros =  [None for _ in range(5)]

        # 1 means 1st round pick, in ALL pick mode, 1: ally 2 heros, 2: opponent 2 heros,
        self.cur_round = 0
        # 3: ally 2 heros, 4: opponent 2 heros
        # 5: ally 1 hero , 6: opponent 1 hero
        # dynamic ban list
        # ban list also contains the picked up heros (so it is more suitable to call it unavailabe hero list)
        self.ban_lst = set()
        # -- end dynamic var --

    def __copy__(self):
        new_node = StateNode(*self.ally_hero_pools, *self.opponent_hero_pools)
        # copy all dynamic var
        new_node.ally_pick_rounds = copy.deepcopy(self.ally_pick_rounds)
        new_node.opponent_pick_rounds = copy.deepcopy(self.opponent_pick_rounds)

        new_node.ally_heros = copy.deepcopy(self.ally_heros)
        new_node.opponent_heros = copy.deepcopy(self.opponent_heros)
        new_node.cur_round = self.cur_round
        new_node.ban_lst = copy.deepcopy(self.ban_lst)
        return new_node

    def ban_hero(self, ban_hero_name):
        """we have two cases, one is directly ban heros, the other one is that we have the pick same hero situation

        Args:
            hero_name (str): ban_hero name
        """
        # pick same hero situation


        if ban_hero_name in self.ally_heros:
            # check if current pick
            ban_hero_index = self.ally_heros.index(ban_hero_name)
            ban_hero_pick_round = self.ally_pick_rounds[ban_hero_index]
            if ban_hero_pick_round != self.cur_round:
                logging.warning(
                    "You cannot ban an hero that is already picked")
                return self
            else:
                # pick same hero situation, remove that hero

                self.ally_heros[ban_hero_index] = None
                self.ally_pick_rounds[ban_hero_index] = 0
                if self.cur_round not in self.ally_pick_rounds:
                    self.cur_round -= 1
                return self
        else:
            # normal ban situation
            if ban_hero_name not in self.ban_lst:
                self.ban_lst.add(ban_hero_name)
            return self

    def _hero_set(self, hero_name, ind, is_ally):
        """this set method will also update pick round
        """
        if is_ally:
            self.ally_heros[ind] = hero_name
            self.ally_pick_rounds[ind] = self.cur_round
        else:
            self.opponent_heros[ind] = hero_name
            self.opponent_pick_rounds[ind] = self.cur_round

        # add name to ban list
        self.ban_lst.add(hero_name)

    def add_hero(self, hero_name, is_ally, position):
        """add hero to either ally or opponent
        update cur round and ban list and hero info

        Args:
            hero_name (_type_): _description_
            position: the natural dota position 1 - 5
        """
        if hero_name is None:
            return
        auto_guess_flag = False
        position_index = 1
        if is_ally:
            checkt_hero_list = self.ally_heros
        else:
            checkt_hero_list = self.opponent_heros
        if position <= 0:
            # meaning we need to auto guess and reorder the positions
            auto_guess_flag = True
            # just find available position
            for check_ind, checkhero in enumerate(checkt_hero_list):
                if checkhero is None:
                    position_index = check_ind
                    break

        else:
            position_index = position - 1  # pythonic index sorry about that

        if checkt_hero_list[position_index] is not None:
            logging.warning(f"Pos {position} has already occupied")
            return

        # check is available
        if hero_name in self.ban_lst:
            logging.warning(f"Hero {hero_name} is not available already")
            return self


        if is_ally:
            # two sit, one is to progress to new round, the other is to achieve current round
            # check if progress to new round
            if self.cur_round in [0, 2, 4] and self.opponent_pick_rounds.count(self.cur_round) >= 2:
                self.cur_round += 1
                # ally hero update
                self._hero_set(hero_name, position_index, is_ally)

            # check if achieve current round
            elif self.cur_round in [1, 3] and self.ally_pick_rounds.count(self.cur_round) == 1:
                # ally hero update
                self._hero_set(hero_name, position_index, is_ally)

            else:
                logging.warning("invalid add ally hero case")
                return self

        else:
            # two sit, one is to progress to new round, the other is to achieve current round
            # check if progress to new round
            if self.cur_round in [1, 3] and self.ally_pick_rounds.count(self.cur_round) == 2:
                self.cur_round += 1
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            # new round case 2
            elif self.cur_round in [5] and self.ally_pick_rounds.count(self.cur_round) == 1:
                self.cur_round += 1
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            # check if achieve current round
            elif self.cur_round in [2, 4] and self.opponent_pick_rounds.count(self.cur_round) == 1:
                # opponent hero update
                self._hero_set(hero_name, position_index, is_ally)

            else:
                logging.warning("invalid add opponent hero case")
                return self

        if auto_guess_flag:
            if is_ally:
                hero_list, hero_round_list = maximum_assignment_heroes(
                    self.get_ally_hero_list(), self.get_ally_hero_pick_round_list())
                self.ally_heros = hero_list
                self.ally_pick_rounds = hero_round_list

            else:
                hero_list, hero_round_list = maximum_assignment_heroes(
                    self.get_opponent_hero_list(), self.get_opponent_hero_pick_round_list())
                self.opponent_heros = hero_list
                self.opponent_pick_rounds = hero_round_list

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

        # get available hero pools
        if self.cur_round in [0, 2, 4]:
            is_ally_next_turn = True
        elif self.cur_round in [1, 3] and self.ally_pick_rounds.count(self.cur_round) == 1:
            is_ally_next_turn = True
        else:
            is_ally_next_turn = False

        if is_ally_next_turn:
            # define hero pool
            hero_pool_lst = self.ally_hero_pools

            hero_list = self.ally_heros

            paired_hero_list = self.opponent_heros

        else:
            hero_pool_lst = self.opponent_hero_pools

            hero_list = self.opponent_heros

            paired_hero_list = self.ally_heros

        # ! to speed up, auto remove a number of worst heros
        # paird hero list filter out PRUNE_WORST_HERO_NUM heros
        # PRUNE_WORST_HERO_NUM
        worst_hero_list = set()
        for paired_hero in paired_hero_list:
            if paired_hero is not None:
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
        if self.cur_round in [1, 3] and self.ally_pick_rounds.count(self.cur_round) == 1:
            # we set a flag and some mods
            pick_same_hero_sit_flag = True
            # next round is still cur_round though we fix one hero input
            next_round = self.cur_round

            fix_hero_pos_ind = self.ally_pick_rounds.index(self.cur_round)
            fix_hero = hero_list[fix_hero_pos_ind]
            fix_hero_pos = fix_hero_pos_ind + 1
            
        # normal case
        if next_round in [1, 2]:
            if pick_same_hero_sit_flag:
                temp_l = []
                for pc in first_round_pick_choice:
                    if fix_hero_pos in pc:
                        temp_l.append(pc)
                if len(temp_l) == 0:
                    # in case it is not normal pos pick
                    temp_l.append([fix_hero_pos, 5])
                first_round_pick_choice = temp_l

            # you can only pick under restriction
            for pick_choice in first_round_pick_choice:
                pc_sorted = pick_choice  # ! assume sort arry for first round
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
            if pick_same_hero_sit_flag:
                available_pos_lst.append(fix_hero_pos)
            available_pos_lst = sorted(available_pos_lst)
            round_pick_choice = list(
                itertools.combinations(available_pos_lst, 2))
            if pick_same_hero_sit_flag:
                temp_l = []
                for pc in round_pick_choice:
                    if fix_hero_pos in pc:
                        temp_l.append(pc)
                round_pick_choice = temp_l

            for pick_choice in round_pick_choice:
                pc_sorted = pick_choice  # ! assume already done after itertools.combination
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
                hero_pick_combo_list = []
                # ! combo list too big, prune it based on with rate matrix
                for a in hero_pool_a:
                    least_combo_heros = []
                    for tempi, w_hero in enumerate(reversed(with_winrate_matrix[a].keys())):
                        if tempi >= PRUNE_WORST_HERO_NUM:
                            break
                        least_combo_heros.append(w_hero)
                    for b in hero_pool_b:
                        if a == b:
                            continue
                        if b in least_combo_heros:
                            continue
                        hero_pick_combo_list.append((a, b))

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
            # # ! --sort the pick_choice_combo_dict may/not help pruning, but trade off between pruning out and sorting ---
            # def measure_counter(combo):
            #     if len(paired_hero_list) > 0:
            #         # random measure
            #         t_ind_hero = random.randint(0,1)
            #         t_ind_pair = random.randint(0,len(paired_hero_list)-1)
            #         return counter_rate_matrix[combo[t_ind_hero]][paired_hero_list[t_ind_pair]]
            #     elif len(combo) == 2:
            #         return with_winrate_matrix[combo[0]][combo[1]]
            #     else:
            #         return 0.0
            # if len(combo_list[0]) == 2:
            #     combo_list = sorted(combo_list, key=measure_counter, reverse=True)
            #     pick_choice_combo_dict[str_pos_pick_choice] = combo_list # store back
            # # ! -----------------------------------------------------

            output_next_nodes_dict[str_pos_pick_choice] = []
            pos_pick_choice = eval(str_pos_pick_choice)  # type: tuple
            for combo in combo_list:  # combo_list is [(hero_a, hero_b)]
                # create new node
                new_node = self.__copy__()
                new_node.cur_round = next_round
                for ind, pos in enumerate(pos_pick_choice):
                    if pick_same_hero_sit_flag:  # add already if pick same hero sit
                        if pos == fix_hero_pos:
                            continue

                    # faster due to no checking
                    new_node._hero_set(combo[ind], is_ally_next_turn, pos-1)

                output_next_nodes_dict[str_pos_pick_choice].append(new_node)
                node_expansion_count += 1
        logging.info(f"node expansion with size {node_expansion_count}")

        return output_next_nodes_dict, pick_choice_combo_dict

    def get_ally_hero_list(self):
        return copy.deepcopy(self.ally_heros)

    def get_opponent_hero_list(self):
        return copy.deepcopy(self.opponent_heros)

    def get_ally_hero_pick_round_list(self):
        return copy.deepcopy(self.ally_pick_rounds)

    def get_opponent_hero_pick_round_list(self):
        return copy.deepcopy(self.opponent_pick_rounds)

    def is_terminated(self):
        if None not in self.ally_heros and None not in self.opponent_heros:
            return True
        else:
            return False

    def __repr__(self) -> str:

        output = ""
        output += "Ally:\n"
        for hero in self.ally_heros:
            output += f"\t{hero}\n"
        output += "Oppo:\n"
        for hero in self.opponent_heros:
            output += f"\t{hero}\n"
        output += f"Current Round: {self.cur_round}\n"
        return output


if __name__ == "__main__":
    # debug
    logging.basicConfig(
        format='%(levelname)s:%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

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

    # start_node = StateNode(*ally_hero_pools, *opponent_hero_pools)
    # output_next_nodes_dict, pick_choice_combo_dict = start_node.next_possible_nodes()
    a = ['Axe', None, None, None, None]
    b = [1,0,0,0,0]
    output = maximum_assignment_heroes(a, b)

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
