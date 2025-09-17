'''
File Created: Tuesday, 17th October 2023 1:51:17 pm
Author: Sukai Huang (huangsukai1997@gmail.com)
-----
Last Modified: Wednesday, 17 September 2025
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
from ordered_set import OrderedSet
import numpy as np
from dota_banpick.config import ALLY_FIRST_ROUND_PICK_CHOICE, OPPO_FIRST_ROUND_PICK_CHOICE, with_winrate_matrix, counter_rate_matrix, lane_rate_info_dict, CAPTAIN_BP_ORDER
from dota_banpick.config import PRUNE_WORST_HERO_NUM, EARLY_STAGE_NOT_CONSIDER_BAN_COMBO
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


class StateNodeCaptain:
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
                 if_bp_first,
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
        
        self.bp_order = CAPTAIN_BP_ORDER
        self.if_bp_first = if_bp_first
        if self.if_bp_first:
            self.ally_id = 'A'
            self.opponent_id = 'B'
        else:
            self.ally_id = 'B'
            self.opponent_id = 'A'

        # dynamic var
        self.ally_pick_rounds = [0 for _ in range(5)] # e.g., [3, 2, 0, 0, 0] means pos 1 picked in round 3, pos 2 picked in round 2
        self.opponent_pick_rounds = [0 for _ in range(5)] # that means index is the position index, value is the round number

        self.ally_heros = [None for _ in range(5)]

        self.opponent_heros =  [None for _ in range(5)]

        # 1 means 1st round bp, in Captain mode, we have 24 rounds, 0 means not start yet,
        self.cur_round = 0
        # dynamic ban list
        # ban list also contains the picked up heros (so it is more suitable to call it unavailabe hero list)
        self.ban_lst = OrderedSet([])
        # -- end dynamic var --

    def __copy__(self):
        new_node = StateNodeCaptain(*self.ally_hero_pools, *self.opponent_hero_pools, self.if_bp_first)
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
        order_code = CAPTAIN_BP_ORDER[self.cur_round]
        _, _, action_code = order_code.split(' ')
        if action_code == 'B':
            # normal ban situation
            if ban_hero_name not in self.ban_lst and ban_hero_name not in self.ally_heros and ban_hero_name not in self.opponent_heros:
                self.ban_lst.add(ban_hero_name)
                self.cur_round += 1
            else:
                logging.warning(f"Hero {ban_hero_name} is not available already")
            return self
        else:
            # invalid ban situation
            logging.warning("You cannot ban at pick round")
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
        if hero_name in self.ban_lst or hero_name in self.ally_heros or hero_name in self.opponent_heros:
            logging.warning(f"Hero {hero_name} is not available already")
            return self

        
        order_code = CAPTAIN_BP_ORDER[self.cur_round]
        _, side_code, action_code = order_code.split(' ')
        if is_ally:
            
            if side_code == self.ally_id and action_code == 'P':
                self.cur_round += 1
            else:
                logging.warning("invalid add ally hero case")
                return self    
    
        else:
            if side_code == self.opponent_id and action_code == 'P':
                self.cur_round += 1
            else:
                logging.warning("invalid add opponent hero case")
                return self
            
        # hero update
        self._hero_set(hero_name, position_index, is_ally)

        if auto_guess_flag:
            if is_ally:
                hero_list, hero_round_list = maximum_assignment_heroes(
                    self.get_ally_hero_list(), self.get_ally_hero_pick_round_list())
                self.ally_heros = hero_list
                self.ally_pick_rounds = hero_round_list

            else:
                # TODO this can add heuristic, e.g., 根据战队的之前的位置习惯进行猜测英雄位置
                hero_list, hero_round_list = maximum_assignment_heroes(
                    self.get_opponent_hero_list(), self.get_opponent_hero_pick_round_list())
                self.opponent_heros = hero_list
                self.opponent_pick_rounds = hero_round_list

        return self

    def next_possible_nodes(self, ally_first_round_pick_choice=ALLY_FIRST_ROUND_PICK_CHOICE, oppo_first_round_pick_choice=OPPO_FIRST_ROUND_PICK_CHOICE):
        """generate a list of possible nodes, based on the current round
        remember the first round pos combo restriction

        Returns: output_next_nodes_dict with structure {str_pick_choice: [StateNodeCaptain]},  
                 pick_choice_combo_dict with structure: {str_pick_choice: [(hero_1, hero_2)]}

        """
        # some properties for next nodes:
        # 1. cur round increase, complete round hero suggestion
        # 2. first 2 rounds pos combo restriction
        # 3. hero pool restricted

        is_ally_next_turn = None
        is_next_a_big_turn = None

        order_code = CAPTAIN_BP_ORDER[self.cur_round]
        _, side_code, action_code = order_code.split(' ')

        if len(CAPTAIN_BP_ORDER) < self.cur_round + 1:
            next_order_code = None
        else:
            next_order_code = CAPTAIN_BP_ORDER[self.cur_round + 1]

        if next_order_code is not None:
            _, next_side_code, next_action_code = next_order_code.split(' ')
        else:
            next_side_code, next_action_code = None, None

        # further think about next next turn
        if len(CAPTAIN_BP_ORDER) < self.cur_round + 2:
            next_next_order_code = None
        else:
            next_next_order_code = CAPTAIN_BP_ORDER[self.cur_round + 2]
        if next_next_order_code is not None:
            _, next_next_side_code, next_next_action_code = next_next_order_code.split(' ')
        else:
            next_next_side_code, next_next_action_code = None, None

        # determine if is_next_a_big_turn is a big turn (meaning next_side_code same as next_next_side_code and they are not None)
        if next_side_code is not None and next_side_code == next_next_side_code:
            is_next_a_big_turn = True
        else:
            is_next_a_big_turn = False


        if next_side_code == self.ally_id:
            is_ally_next_turn = True
        elif next_side_code == self.opponent_id:
            is_ally_next_turn = False
        else:
            is_ally_next_turn = False

        if is_ally_next_turn:
            # define hero pool to be the ally hero pool
            hero_pool_lst = self.ally_hero_pools

            hero_list = self.ally_heros

            paired_hero_list = self.opponent_heros

            paired_pool_lst = self.opponent_hero_pools

        else:
            hero_pool_lst = self.opponent_hero_pools

            hero_list = self.opponent_heros

            paired_hero_list = self.ally_heros

            paired_pool_lst = self.ally_hero_pools

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
            # also remove already picked hero
            for picked_hero in hero_list:
                if picked_hero in pool_copy:
                    pool_copy.remove(picked_hero)
            for picked_hero in paired_hero_list:
                if picked_hero in pool_copy:
                    pool_copy.remove(picked_hero)

            filtered_hero_pool_lst.append(pool_copy)

        filtered_paired_pool_lst = []
        for pool in paired_pool_lst:
            pool_copy = copy.deepcopy(pool)
            for unavailable_hero in self.ban_lst:
                if unavailable_hero in pool_copy:
                    pool_copy.remove(unavailable_hero)
            # also remove already picked hero
            for picked_hero in paired_hero_list:
                if picked_hero in pool_copy:
                    pool_copy.remove(picked_hero)
            for picked_hero in hero_list:
                if picked_hero in pool_copy:
                    pool_copy.remove(picked_hero)
            filtered_paired_pool_lst.append(pool_copy)


        # check available combo
        # make copy first and then use add hero function in the new instance
        next_round = self.cur_round + 1
        # structure: {pick_choice: [(hero_1, hero_2)]}, later flatten it to have list of nodes
        pick_choice_combo_dict = None

        if next_action_code == 'P':
            pick_choice_combo_dict = dict() # ! pick_choice_combo_dict control the possible next nodes
            # case 1: big turn
            # case 2: small turn
            if is_next_a_big_turn:
                # means it must be small turn
                # get the last available pos
                # you need to check what pos combo is available
                available_pos_lst = [] 
                if is_ally_next_turn:
                    for sublist in ally_first_round_pick_choice:
                        available_pos_lst.extend(sublist)
                else:
                    for sublist in oppo_first_round_pick_choice:
                        available_pos_lst.extend(sublist)
                available_pos_lst = sorted(list(set(available_pos_lst)))
                round_pick_choice = list(
                    itertools.combinations(available_pos_lst, 1))
                


            else:
                # you need to check what pos combo is available
                available_pos_lst = []  # natural dota position number 1-5
                for ind in range(len(hero_list)):
                    if hero_list[ind] is None:
                        available_pos_lst.append(ind + 1)
            
                available_pos_lst = sorted(available_pos_lst)
                # check if big or small turn
                if is_next_a_big_turn:
                    round_pick_choice = list(
                        itertools.combinations(available_pos_lst, 2))
                else:
                    # get the last available pos
                    # you need to check what pos combo is available
                    round_pick_choice = list(
                        itertools.combinations(available_pos_lst, 1))
                    
            # you can only pick under restriction
            for pick_choice in round_pick_choice:
                pc_sorted = pick_choice  # ! assume sort arry for first round
            
                pick_indexs = [x - 1 for x in pc_sorted]  # pythonic index
                picked_hero_pools = [filtered_hero_pool_lst[pick_ind] for pick_ind in pick_indexs]
    
                
                hero_pick_combo_list = itertools.product(*picked_hero_pools)
                hero_pick_combo_list = [x for x in hero_pick_combo_list if len(set(x)) == len(x)]
                pick_choice_combo_dict[str(pc_sorted)] = hero_pick_combo_list 

        # consider ban combos, consider paired_hero_list 

        ban_choice_combo_dict = None
        if next_action_code == 'B':
            ban_choice_combo_dict = dict()
            # you need to check what pos combo is available
            available_pos_lst = []  # natural dota position number 1-5
            for ind in range(len(paired_hero_list)):
                if paired_hero_list[ind] is None:
                    available_pos_lst.append(ind + 1)
        
            available_pos_lst = sorted(available_pos_lst)

            if next_round == 1:
                round_ban_choice = list(
                itertools.combinations(available_pos_lst, 2))
            else:
                round_ban_choice = list(
                    itertools.combinations(available_pos_lst, 1))
            
            # if next round < 9, then remove (1, 4), (3, 5), (4, 5) combo
            if next_round < 9:
                round_ban_choice = [x for x in round_ban_choice if x not in EARLY_STAGE_NOT_CONSIDER_BAN_COMBO]

            for ban_choice in round_ban_choice:
                bc_sorted = ban_choice  # ! assume sort arry for first round
                ban_indexs = [x - 1 for x in bc_sorted]  # pythonic index
                ban_hero_pools = [filtered_paired_pool_lst[ban_ind] for ban_ind in ban_indexs]
                ban_hero_combo_list = itertools.product(*ban_hero_pools)
                ban_hero_combo_list = [x for x in ban_hero_combo_list if len(set(x)) == len(x)]
                ban_choice_combo_dict[str(bc_sorted)] = ban_hero_combo_list

            
                

        # now we have the pick_choice_combo_dict, flatten it and generate new nodes. also return pick_choice_combo_dict
        # output_next_nodes_dict with structure {str_pick_choice: [StateNodeCaptain]},

        output_next_nodes_dict = dict()
        node_expansion_count = 0
        if pick_choice_combo_dict is not None: # ! pick turn
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
                    # new node cur round will be next round if small turn, or next next round if big turn
                    if is_next_a_big_turn:
                        new_node.cur_round = next_round + 1
                    else:
                        new_node.cur_round = next_round
                    for ind, pos in enumerate(pos_pick_choice):

                        # faster due to no checking
                        new_node._hero_set(combo[ind], pos-1, is_ally_next_turn)

                    output_next_nodes_dict[str_pos_pick_choice].append(new_node)
                    node_expansion_count += 1
            logging.info(f"node expansion with size {node_expansion_count}")

            return output_next_nodes_dict, pick_choice_combo_dict
        else: 
            assert ban_choice_combo_dict is not None
            for str_pos_ban_choice, combo_list in ban_choice_combo_dict.items():
                output_next_nodes_dict[str_pos_ban_choice] = []
                pos_ban_choice = eval(str_pos_ban_choice)  # type: tuple
                for combo in combo_list:  # combo_list is [(hero_a, hero_b)]
                    # create new node
                    new_node = self.__copy__()
                    # new node cur round will be next round if small turn, or next next round if big turn
                    if is_next_a_big_turn:
                        new_node.cur_round = next_round + 1
                    else:
                        new_node.cur_round = next_round
                    for ind, pos in enumerate(pos_ban_choice):
                        
                        # faster due to no checking
                        new_node.ban_hero(combo[ind])
                    output_next_nodes_dict[str_pos_ban_choice].append(new_node)
                    node_expansion_count += 1
            logging.info(f"node expansion with size {node_expansion_count}")
            return output_next_nodes_dict, ban_choice_combo_dict

    def get_ally_hero_list(self):
        return copy.deepcopy(self.ally_heros)

    def get_opponent_hero_list(self):
        return copy.deepcopy(self.opponent_heros)
    
    def get_ban_hero_list(self):
        return copy.deepcopy(list(self.ban_lst))

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
        output += "Bans:\n"
        output += str(self.ban_lst)
        output += "\n"
        output += f"Current Round: {self.cur_round}\n"
        # add if first pick
        output += f"Ally First Pick: {self.if_bp_first}\n"
        output += str(self.ally_hero_pools)
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

    # start_node = StateNodeCaptain(*ally_hero_pools, *opponent_hero_pools)
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
