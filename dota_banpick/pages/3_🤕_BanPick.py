import streamlit as st
from glob import glob
import json
import os
from natsort import natsorted
import streamlit as st
from multiprocessing import Manager
import copy
import pandas as pd
import pickle
from PIL import Image
from dota_banpick.alphabeta import alphabeta
from dota_banpick.heuristic import compute_associated_ban_suggestion_first_round, compute_bad_picks_for_each_pos
from dota_banpick.pickaction import StateNode
from dota_banpick.config import DEPTH_LIMIT, FIRST_ROUND_PICK_CHOICE
import pandas as pd

from dota_banpick.st_cache import get_heros, pos_description, get_hero_csv_data_raw, get_name_abbrev_dict, get_hero_csv_data, get_image_data, init_warmup_cache_dict, load_cached_name_hero_pool_dict, load_default_hero_pools

image_width = 11
suggest_num = 5


def row_display_component(component_arg_list, width, show_compo_func):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_compo_func(*args)


def show_image_compo(img, name):
    st.image(img, caption=name,  use_column_width="always")


def show_item_component(img, name):
    st.text_input("status", label_visibility="hidden", max_chars=2,
                  key=f"bpinput_{name}", on_change=inp_on_change, args=(f"bpinput_{name}", name))
    st.image(img, caption=name,  use_column_width="always")


def inp_on_change(bpinput_key, name):
    input_val = st.session_state[bpinput_key]
    if len(input_val) > 0:
        p_type = input_val[0]
        if len(input_val) == 2 and p_type == "a":
            pos_v = int(input_val[1])
            st.session_state.banpicknode.add_hero(name, True, pos_v)
        elif len(input_val) == 2 and (p_type == "o" or p_type == "e"):
            pos_v = int(input_val[1])
            st.session_state.banpicknode.add_hero(name, False, pos_v)
        elif p_type == "b" or p_type == "q":
            st.session_state.banpicknode.ban_hero(name)


def show_player_selectoption(playername):
    player_cache_dict = load_cached_name_hero_pool_dict()
    st.header(playername)
    selectoption = st.selectbox("Choose position",
                                options=pos_description, index=None, key=f"choose_pos_{playername}")
    if selectoption:
        pos_ind = pos_description.index(selectoption)
        # remove other playername
        for pos in st.session_state['available_positions']:
            if st.session_state['available_positions'][pos] == playername:
                st.session_state['available_positions'][pos] = None
        # add current
        st.session_state['available_positions'][selectoption] = playername

        # now, add ally_hero_pools and inform some warnings
        player_hero_pool = player_cache_dict[playername]['target_hero_pool']
        player_avail_hero_pool = [
            x for x in player_hero_pool if x in st.session_state['opponent_hero_pools'][pos_ind]]
        st.session_state["ally_hero_pools"][pos_ind] = player_avail_hero_pool
        if len(player_avail_hero_pool) < 5:
            st.warning(
                f"{playername}'s hero size for {selectoption.split(' ')[-1]} is {len(player_avail_hero_pool)}")
        else:
            st.info(
                f"{playername}'s hero size for {selectoption.split(' ')[-1]} is {len(player_avail_hero_pool)}")


def convert_pos_choice_to_readable_lst(str_pos_choice):
    poses = eval(str_pos_choice)
    pos_inds = [x-1 for x in poses]
    output_list = []
    for pos_ind, posname in enumerate(st.session_state['available_positions']):
        if pos_ind in pos_inds:
            if st.session_state['available_positions'][posname] is None:
                output_list.append(f"{' '.join(posname.split(' ')[:2])} ")
            else:
                output_list.append(
                    f"{' '.join(posname.split(' ')[:2])} {st.session_state['available_positions'][posname]}*")

    return output_list


def get_impacted_player_from_choice(str_pos_choice):
    poses = eval(str_pos_choice)
    pos_inds = [x-1 for x in poses]
    output_list = []
    for pos_ind, posname in enumerate(st.session_state['available_positions']):
        if pos_ind in pos_inds:
            if st.session_state['available_positions'][posname] is not None:
                output_list.append(
                    st.session_state['available_positions'][posname])

    return output_list


def form_pick_ban_table(pick_list, ban_list, str_pick_choice):
    cols_name = convert_pos_choice_to_readable_lst(str_pick_choice)
    cols_name.append("Suggested Bans")
    if len(pick_list[0]) == 2:
        player_a_list = [x for x, _ in pick_list]
        player_b_list = [y for _, y in pick_list]
        outputtable = dict()
        outputtable[cols_name[0]] = player_a_list
        outputtable[cols_name[1]] = player_b_list
        outputtable[cols_name[2]] = ban_list
        return outputtable
    else:
        player_a_list = [x for x, in pick_list]
        outputtable = dict()
        outputtable[cols_name[0]] = player_a_list
        outputtable[cols_name[1]] = ban_list
        return outputtable

def form_pick_avoid_table(pick_list, str_pick_choice):
    cols_name = convert_pos_choice_to_readable_lst(str_pick_choice)
    if len(pick_list[0]) == 2:
    
        player_a_list = [x for x, _ in pick_list]
        player_b_list = [y for _, y in pick_list]
        outputtable = dict()
        outputtable[cols_name[0]] = player_a_list
        outputtable[cols_name[1]] = player_b_list
        return outputtable
    else:
        player_a_list = [x for x, in pick_list]
        outputtable = dict()
        outputtable[cols_name[0]] = player_a_list
        return outputtable



def update_ban_hero_multiselect():
    banlist = st.session_state["ban_multiselect"]
    imgfilenames = list(
        st.session_state['raw_df']['Image filename'].loc[banlist].str.strip())
    img_array = get_image_data(imgfilenames)
    st.session_state['ban_image_args_list'] = list(
        zip(img_array, [None for _ in range(len(banlist))]))

    if "the_bp_node" in st.session_state:
        for banhero in banlist:
            st.session_state.the_bp_node.ban_hero(banhero)

    # update placeholder stuffs
    if "Preparation Drafting" in st.session_state.suggest_header_placeholder:
        val, prepara_phase_suggested_pick_dict = alphabeta(
            st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, alpha_beta_cache_dict)
        prepare_phase_suggested_ban_dict = compute_associated_ban_suggestion_first_round(
            prepara_phase_suggested_pick_dict)

        for ind, comboname in enumerate(prepara_phase_suggested_pick_dict):
            impacted_player_lst = get_impacted_player_from_choice(
                comboname)
            if len(impacted_player_lst) > 0:
                st.session_state[
                    f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname} for {' and '.join(impacted_player_lst)}"
            else:
                st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname}"

            pick_list = [
                x for x, _ in prepara_phase_suggested_pick_dict[comboname]][:suggest_num]
            ban_list = [
                x for x in prepare_phase_suggested_ban_dict[comboname]][:suggest_num]
            pick_ban_table = form_pick_ban_table(
                pick_list, ban_list, comboname)
            st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table

        # remove further table
        while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
            ind += 1
            
    else:
        val, prepara_phase_suggested_pick_dict = alphabeta(
            st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, None)

        for ind, comboname in enumerate(prepara_phase_suggested_pick_dict):
            impacted_player_lst = get_impacted_player_from_choice(
                comboname)
            if len(impacted_player_lst) > 0:
                st.session_state[
                    f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname} for {' and '.join(impacted_player_lst)}"
            else:
                st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname}"

            pick_list = [
                x for x, _ in prepara_phase_suggested_pick_dict[comboname]][:suggest_num]

            pick_avoid_table = form_pick_avoid_table(
                pick_list, comboname)
            st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_avoid_table

        # remove further table
        while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
            ind += 1
        

def update_pick_hero_oppo_multiselect():
    oppopicklist = st.session_state['oppo_multiselect']
    # filter ban list, which including selected unavailable ones
    oppopicklist = [x for x in oppopicklist if x not in st.session_state.the_bp_node.ban_lst]
    for opohero in oppopicklist:
        st.session_state.the_bp_node.add_hero(opohero, False, -1)
        nonecount = st.session_state.the_bp_node.opponent_heros.count(None)

        if nonecount in [3,1]:
            if nonecount == 3 :
                st.session_state.suggest_header_placeholder = "2nd Round Drafting Suggestion"
            elif nonecount == 1:
                st.session_state.suggest_header_placeholder = "Final Round Drafting Suggestion"
            st.session_state.info_placeholder = ("Try to conter the picked ones and avoid picking bad heroes.")
            val, prepara_phase_suggested_pick_dict = alphabeta(
                st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, None)
            
            output_dict = compute_bad_picks_for_each_pos(st.session_state.the_bp_node)
            st.session_state.bad_picks_for_each_pos = output_dict

            for ind, comboname in enumerate(prepara_phase_suggested_pick_dict):
                impacted_player_lst = get_impacted_player_from_choice(
                    comboname)
                if len(impacted_player_lst) > 0:
                    st.session_state[
                        f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname} for {' and '.join(impacted_player_lst)}"
                else:
                    st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname}"

                pick_list = [
                    x for x, _ in prepara_phase_suggested_pick_dict[comboname]][:suggest_num]

                pick_sugg_table = form_pick_avoid_table(
                    pick_list, comboname)
                st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_sugg_table

            # remove further table
            while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
                ind += 1
            
            
    
def ready_to_bp_on_click():
    # ------  preparation phase suggestion ------
    st.session_state.ally_name_list = []
    for pos_ind, posname in enumerate(st.session_state['available_positions']):
        if st.session_state['available_positions'][posname] is not None:
            st.session_state.ally_name_list.append(
                st.session_state['available_positions'][posname])
        else:
            st.session_state.ally_name_list.append(
                " ".join(posname.split(" ")[:2]))

    st.session_state.all_hero_list = get_heros()
    st.session_state.the_bp_node = StateNode(
        *st.session_state["ally_hero_pools"], *st.session_state["opponent_hero_pools"])

    st.session_state['ban_image_args_list'].clear()

    st.session_state.suggest_header_placeholder = "Preparation Drafting Suggestion"
    st.session_state.info_placeholder = ("In preparation phase, we only suggest Combos for Pos 3, 4 and 5."
                                         " This guidance stems from our assessment that Positions 1 and 2 should avoid early picks to reduce the risk of easy counters.")

    val, prepara_phase_suggested_pick_dict = alphabeta(
        st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, alpha_beta_cache_dict)
    prepare_phase_suggested_ban_dict = compute_associated_ban_suggestion_first_round(
        prepara_phase_suggested_pick_dict)

    for ind, comboname in enumerate(prepara_phase_suggested_pick_dict):
        impacted_player_lst = get_impacted_player_from_choice(
            comboname)
        if len(impacted_player_lst) > 0:
            st.session_state[
                f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname} for {' and '.join(impacted_player_lst)}"
        else:
            st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname}"

        pick_list = [
            x for x, _ in prepara_phase_suggested_pick_dict[comboname]][:suggest_num]
        ban_list = [
            x for x in prepare_phase_suggested_ban_dict[comboname]][:suggest_num]
        pick_ban_table = form_pick_ban_table(
            pick_list, ban_list, comboname)
        st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table


if __name__ == "__main__":
    st.set_page_config(
        layout="wide"
    )

    st.markdown("""
    <style>
    .small-font {
        font-size:11px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if "opponent_hero_pools" not in st.session_state:
        st.session_state["opponent_hero_pools"] = load_default_hero_pools()
        # remove smurf heroes, by default we do not consider them at early stage
        for i in range(len(st.session_state["opponent_hero_pools"])):
            if "Meepo" in st.session_state["opponent_hero_pools"][i]:
                st.session_state["opponent_hero_pools"][i].remove("Meepo")
            if "Visage" in st.session_state["opponent_hero_pools"][i]:
                st.session_state["opponent_hero_pools"][i].remove("Visage")
            if "Arc Warden" in st.session_state["opponent_hero_pools"][i]:
                st.session_state["opponent_hero_pools"][i].remove("Arc Warden")
            if "Chen" in st.session_state["opponent_hero_pools"][i]:
                st.session_state["opponent_hero_pools"][i].remove("Chen")

    if "ally_hero_pools" not in st.session_state:
        st.session_state["ally_hero_pools"] = load_default_hero_pools()

    if "ban_image_args_list" not in st.session_state:
        st.session_state["ban_image_args_list"] = []

    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = get_hero_csv_data_raw()

    if 'name_abbrev_dict' not in st.session_state:
        st.session_state['name_abbrev_dict'] = get_name_abbrev_dict()
        st.session_state['name_abbrev_dict_keys_list'] = list(
            st.session_state['name_abbrev_dict'].keys())

    ready_to_bp = False
    st.title("Refresh (F5) the page if you want to BP your next game!")
    player_cache_dict = load_cached_name_hero_pool_dict()
    alpha_beta_cache_dict = init_warmup_cache_dict()

    # available position
    if "available_positions" not in st.session_state:
        od = dict()
        for pos in pos_description:
            od[pos] = None  # structure {posname: playername}
        st.session_state['available_positions'] = od

    # -- sidebar select player ---
    with st.sidebar:
        if len(player_cache_dict) == 0:
            st.warning(
                "Cannot find player hero pool in cache, please create one first!")
        else:
            # show the player and ask to select position
            plyername_arg_list = [(playername,)
                                  for playername in player_cache_dict]
            row_display_component(plyername_arg_list, 2,
                                  show_player_selectoption)

            with st.expander("Team info", expanded=True):
                st.table(st.session_state['available_positions'])

            confirmteambut = st.button(
                "Confirm your team structure", type="primary", use_container_width=True, on_click=ready_to_bp_on_click)

    # ---------------Table Placeholder -------------------
    if "suggest_header_placeholder" in st.session_state:
        st.subheader(st.session_state.suggest_header_placeholder)
        st.info(st.session_state.info_placeholder)
        with st.container():
            col_ind_c = 0
            while f"suggest_ban_table_col_{col_ind_c}_table" in st.session_state:
                col_ind_c += 1
            combocols = st.columns(col_ind_c, gap="large")
            for ind in range(len(combocols)):
                with combocols[ind]:
                    st.info(
                        st.session_state[f"suggest_ban_table_col_{ind}_table_header"])
                    st.table(
                        st.session_state[f"suggest_ban_table_col_{ind}_table"])
        if "bad_picks_for_each_pos" in st.session_state:
            bad_picks_for_each_pos = st.session_state.bad_picks_for_each_pos
            badpick_cols = st.columns(len(bad_picks_for_each_pos))
            for ind, playerpos in enumerate(bad_picks_for_each_pos):
                with badpick_cols[ind]:
                    st.warning(f"Bad picks for {playerpos}")
                    st.table(bad_picks_for_each_pos[playerpos])

    # ----------------- BAN  LIST --------------------------------
    if "suggest_header_placeholder" in st.session_state:
    
        st.subheader("Ban List")
        bancols = st.columns(2)
        with bancols[0]:
            st.multiselect("Input Banned Heroes",
                        options=st.session_state['name_abbrev_dict_keys_list'],
                        format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                        key="ban_multiselect", placeholder="Ban a hero",
                        on_change=update_ban_hero_multiselect)
        with bancols[1]:
            with st.expander("Display", expanded=True):
                st.empty()
                row_display_component(
                    st.session_state['ban_image_args_list'], 6, show_image_compo)

    # -----------------------------------------------------------
    # --------------- Pick -------------------------------
    if "ally_name_list" in st.session_state:
        st.subheader("Pick List")
        ally_pick_column, oppo_pick_column = st.columns(2)

        with ally_pick_column:
            ally_name_list = st.session_state.ally_name_list
            ally_hero_display_cols = st.columns(5)
            for ally_ind in range(len(ally_hero_display_cols)):
                with ally_hero_display_cols[ally_ind]:
                    sloutput = st.selectbox(f"Ally {ally_name_list[ally_ind]}",
                                            options=st.session_state['name_abbrev_dict_keys_list'],
                                            format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                                            index=None,
                                            key=f"hero_pick_selectbox_{ally_name_list[ally_ind]}")
                    if sloutput:
                        st.session_state.suggest_header_placeholder = "Input Picked Heroes Phase"
                        st.session_state.info_placeholder = ("Add ally heroes first, and then opponent heroes.")
                        st.session_state.the_bp_node.add_hero(
                            sloutput, True, ally_ind+1)
                    with st.expander("Display", expanded=True):
                        st.empty()
                        target_hero_in_node = st.session_state.the_bp_node.ally_heros[ally_ind]
                        if target_hero_in_node is not None:
                            imgfilenames = [st.session_state['raw_df']
                                            ['Image filename'].loc[target_hero_in_node].strip()]
                            img = get_image_data(imgfilenames)
                            st.image(img, caption=target_hero_in_node,
                                     use_column_width="always")

        with oppo_pick_column:
            # multiselect box for selecting oppo because we dont know their pos
            st.multiselect("Input Opponent Heroes",
                           options=st.session_state['name_abbrev_dict_keys_list'],
                           format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                           key="oppo_multiselect", placeholder="Pick opponent heroes",
                           on_change=update_pick_hero_oppo_multiselect)

            oppo_name_list = [" ".join(x.split(" ")[:2])
                              for x in pos_description]
            oppo_hero_display_cols = st.columns(5)
            for oppo_ind in range(len(oppo_hero_display_cols)):
                with oppo_hero_display_cols[oppo_ind]:
                    with st.expander(f"Oppo {oppo_name_list[oppo_ind]}", expanded=True):
                        st.empty()
                        target_hero_in_node = st.session_state.the_bp_node.opponent_heros[oppo_ind]
                        if target_hero_in_node is not None:
                            imgfilenames = [st.session_state['raw_df']
                                            ['Image filename'].loc[target_hero_in_node].strip()]
                            img = get_image_data(imgfilenames)
                            st.image(img, caption=target_hero_in_node,
                                     use_column_width="always")
