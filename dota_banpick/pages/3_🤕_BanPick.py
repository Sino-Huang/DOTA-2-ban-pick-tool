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
from streamlit_extras.image_in_tables import table_with_images
from dota_banpick.config import DEPTH_LIMIT, ALLY_FIRST_ROUND_PICK_CHOICE, UNCOMMON_HEROES
import pandas as pd
from streamlit.errors import StreamlitAPIException
from dota_banpick.st_cache import load_alpha_beta_cache_dict, record_folder, get_heros, pos_description, get_hero_csv_data_raw, get_name_abbrev_dict, get_hero_csv_data, get_image_data, load_cached_name_hero_pool_dict, load_default_hero_pools
import subprocess
from subprocess import PIPE
import time

image_width = 11
suggest_num = 5

def pipe_alphabeta(*thein):
    start_time = time.time()
    # subprocess version
    # thein = pickle.dumps(thein)
    # p = subprocess.Popen(["python", "-m", "dota_banpick.alphabeta"],
    #                            stdout=PIPE, stdin=PIPE, stderr=PIPE)
    # stdout_data = p.communicate(input=thein)[0]
    # output = pickle.loads(stdout_data)
    # normal version
    ab_cache_dict = load_alpha_beta_cache_dict()
    # ab_cache_dict = None
    output = alphabeta(*thein, ab_cache_dict)
    end_time = time.time()
    st.toast(f"Process Time: {end_time - start_time:3f} sec.")
    return output 

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


def get_online_image_urls(heronames):
    imgfilenames = list(
        st.session_state['raw_df']['Image filename'].loc[list(heronames)].str.strip())
    lst = [
        f'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{x}.png' for x in imgfilenames]
    return lst


def get_diverse_suggest_lst(sugest_lst, limit, occur_num = 2):
    output_list = []
    occur_list = []
    outputinds = [] 
    for ind, comb in enumerate(sugest_lst):
        dontuse_flag = False
        for h in comb:
            if occur_list.count(h) >= occur_num:
                dontuse_flag = True
                break
        if not dontuse_flag:
            output_list.append(comb)
            outputinds.append(ind)
            for h in comb:
                occur_list.append(h)
        if len(output_list) >= limit:
            break
    return output_list, outputinds


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
    unziplist = list(zip(*pick_list))
    outputtable = dict()

    for i, lst in enumerate(unziplist):
        # convert lst to image urls
        lst = get_online_image_urls(lst)
        # -----------
        outputtable[cols_name[i]] = lst
    outputtable[cols_name[-1]] = ban_list
    return outputtable


def form_pick_avoid_table(pick_list, str_pick_choice):
    cols_name = convert_pos_choice_to_readable_lst(str_pick_choice)
    unziplist = list(zip(*pick_list))
    outputtable = dict()
    for i, lst in enumerate(unziplist):
        # convert lst to image urls
        lst = get_online_image_urls(lst)
        # -----------
        outputtable[cols_name[i]] = lst
    return outputtable

def myprint(num):
    print(num)
    
def update_ban_hero_multiselect():

    banlist = st.session_state["ban_multiselect"]
    if "the_bp_node" in st.session_state:
        banlst_num_before = len(st.session_state.the_bp_node.ban_lst)
        for banhero in banlist:
            st.session_state.the_bp_node.ban_hero(banhero)
        banlst_num_after = len(st.session_state.the_bp_node.ban_lst)
        if banlst_num_before == banlst_num_after:
            return
    
    imgfilenames = list(
        st.session_state['raw_df']['Image filename'].loc[list(st.session_state.the_bp_node.ban_lst)].str.strip())
    img_array = get_image_data(imgfilenames)
    st.session_state['ban_image_args_list'] = list(
        zip(img_array, [None for _ in range(len(banlist))]))

    if st.session_state.the_bp_node.ally_heros.count(None) != 0:
        # update placeholder stuffs
        if "Preparation Drafting" in st.session_state.suggest_header_placeholder:
            with st.spinner("AI Searching..."):
                val, prepara_phase_suggested_pick_dict = pipe_alphabeta(
                    st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, True)
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
                    x for x, _ in prepara_phase_suggested_pick_dict[comboname]]
                pick_list, pick_list_inds = get_diverse_suggest_lst(pick_list, suggest_num)

                ban_list = [
                    x for x in prepare_phase_suggested_ban_dict[comboname]]
                ban_list = [ban_list[x] for x in pick_list_inds]
                pick_ban_table = form_pick_ban_table(
                    pick_list, ban_list, comboname)
                st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table

            # remove further table
            while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
                ind += 1

        else:
            with st.spinner("AI Searching..."):
                val, prepara_phase_suggested_pick_dict = pipe_alphabeta(
                    st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, True)

            for ind, comboname in enumerate(prepara_phase_suggested_pick_dict):
                impacted_player_lst = get_impacted_player_from_choice(
                    comboname)
                if len(impacted_player_lst) > 0:
                    st.session_state[
                        f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname} for {' and '.join(impacted_player_lst)}"
                else:
                    st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"Pos Combo {comboname}"

                pick_list = [
                    x for x, _ in prepara_phase_suggested_pick_dict[comboname]]
                pick_list, _ = get_diverse_suggest_lst(pick_list, suggest_num)

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
    oppopicklist = [
        x for x in oppopicklist if x not in st.session_state.the_bp_node.ban_lst]
    nonecount_before = st.session_state.the_bp_node.opponent_heros.count(None)
    for opohero in oppopicklist:
        st.session_state.the_bp_node.add_hero(opohero, False, -1)
        nonecount = st.session_state.the_bp_node.opponent_heros.count(None)

        if nonecount in [3, 1]:
            if nonecount == 3:
                st.session_state.suggest_header_placeholder = "2nd Round Drafting Suggestion"
            elif nonecount == 1:
                st.session_state.suggest_header_placeholder = "Final Round Drafting Suggestion"
            st.session_state.info_placeholder = (
                "Try to conter the picked ones and avoid picking bad heroes.")
            if nonecount_before != nonecount:
                with st.spinner("AI Searching..."):
                    val, prepara_phase_suggested_pick_dict = pipe_alphabeta(
                        st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, True)

                output_dict = compute_bad_picks_for_each_pos(
                    st.session_state.the_bp_node, suggest_num)
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
                        x for x, _ in prepara_phase_suggested_pick_dict[comboname]]
                    pick_list, _ = get_diverse_suggest_lst(pick_list, suggest_num)

                    pick_sugg_table = form_pick_avoid_table(
                        pick_list, comboname)
                    st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_sugg_table

                # remove further table
                while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
                    del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
                    del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
                    ind += 1


def ally_pick_select(select_key, ally_ind):
    selectedhero = st.session_state[select_key]
    st.session_state.suggest_header_placeholder = "Refresh (F5) to BP your next game."
    st.session_state.info_placeholder = (
        "Add ally heroes first, and then opponent heroes.")
    st.session_state.the_bp_node.add_hero(
        selectedhero, True, ally_ind+1)
    
    if st.session_state.the_bp_node.ally_heros.count(None) in [4, 2]:
        val, prepara_phase_suggested_pick_dict = pipe_alphabeta(
            st.session_state.the_bp_node, 0, -999, 999, True, 0, False)
        prepare_phase_suggested_ban_dict = None 
        if st.session_state.the_bp_node.ally_heros.count(None) == 4:   
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
                x for x, _ in prepara_phase_suggested_pick_dict[comboname]]
            pick_list, pick_list_inds = get_diverse_suggest_lst(pick_list, suggest_num, suggest_num)
            if prepare_phase_suggested_ban_dict is not None:
                ban_list = [
                    x for x in prepare_phase_suggested_ban_dict[comboname]]
                ban_list = [ban_list[x] for x in pick_list_inds]
                pick_ban_table = form_pick_ban_table(
                    pick_list, ban_list, comboname)
            else:
                pick_ban_table = form_pick_avoid_table(
                    pick_list, comboname)
            st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table
        # remove further table
        while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
            ind += 1


def ready_to_bp_on_click():
    # save cache dict ab
    # ab_cache_dict = load_alpha_beta_cache_dict()
    ab_cache_dict = None
    if ab_cache_dict is not None:
        with open(os.path.join(record_folder, 'depth_limit_1_warmup_cache_dict.pkl'), 'wb') as f:
            pickle.dump(dict(ab_cache_dict), f)
            
    # ------  preparation phase suggestion ------
    st.session_state.ally_name_list = []
    for pos_ind, posname in enumerate(st.session_state['available_positions']):
        if st.session_state['available_positions'][posname] is not None:
            st.session_state.ally_name_list.append(
                st.session_state['available_positions'][posname])
        else:
            st.session_state.ally_name_list.append(
                " ".join(posname.split(" ")[:2]))
    if 'bad_picks_for_each_pos' in st.session_state:
        del st.session_state.bad_picks_for_each_pos 
    
    # remove further table
    tt = 0
    while f"suggest_ban_table_col_{tt}_table" in st.session_state:
        del st.session_state[f"suggest_ban_table_col_{tt}_table"]
        del st.session_state[f"suggest_ban_table_col_{tt}_table_header"]
        tt += 1    
    
    st.session_state.all_hero_list = get_heros()
    st.session_state.the_bp_node = StateNode(
        *st.session_state["ally_hero_pools"], *st.session_state["opponent_hero_pools"])

    st.session_state['ban_image_args_list'].clear()

    st.session_state.suggest_header_placeholder = "Preparation Drafting Suggestion"
    st.session_state.info_placeholder = ("In preparation phase, we only suggest Combos for Pos 3, 4 and 5."
                                         " This guidance stems from our assessment that Positions 1 and 2 should avoid early picks to reduce the risk of easy counters.")
    with st.spinner("AI Searching..."):
        val, prepara_phase_suggested_pick_dict = pipe_alphabeta(
            st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT, True)
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
            x for x, _ in prepara_phase_suggested_pick_dict[comboname]]
        pick_list, pick_list_inds = get_diverse_suggest_lst(pick_list, suggest_num)

        ban_list = [
                    x for x in prepare_phase_suggested_ban_dict[comboname]]
        ban_list = [ban_list[x] for x in pick_list_inds]
        pick_ban_table = form_pick_ban_table(
            pick_list, ban_list, comboname)
        st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table


if __name__ == "__main__":
    try:
        st.set_page_config(
            layout="wide"
        )
    except StreamlitAPIException:
        pass

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
            for dontcarehero in UNCOMMON_HEROES:
                if dontcarehero in st.session_state["opponent_hero_pools"][i]:
                    st.session_state["opponent_hero_pools"][i].remove(dontcarehero)

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
    st.title("D2BP")
    player_cache_dict = load_cached_name_hero_pool_dict()

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
            if "bad_picks_for_each_pos" in st.session_state:
                combocols = st.columns([1.0 for _ in range(col_ind_c)] + [1.5], gap="small")
            else:
                combocols = st.columns(col_ind_c, gap="small")
            for ind in range(col_ind_c):
                with combocols[ind]:
                    st.info(
                        st.session_state[f"suggest_ban_table_col_{ind}_table_header"])
                    target_table = pd.DataFrame(
                        st.session_state[f"suggest_ban_table_col_{ind}_table"])
                    # st.dataframe(target_table)
                    st.markdown(table_with_images(df=target_table, url_columns=list(
                        target_table.keys())[:2]), unsafe_allow_html=True)

            if "bad_picks_for_each_pos" in st.session_state:
                with combocols[-1]:
                    st.info("Bad Heroes After Opponent Picks")
                    bad_picks_for_each_pos = st.session_state.bad_picks_for_each_pos
                    not_picked_inds = []
                    for tti, h in enumerate(st.session_state.the_bp_node.ally_heros):
                        if h is None:
                            not_picked_inds.append(tti)
                    if len(not_picked_inds) > 0:
                        badpick_cols = st.columns(len(not_picked_inds))
                        target_bad_table = dict()
                        for ttttti, sugbanind in enumerate(not_picked_inds):
                            with badpick_cols[ttttti]:
                                lst = get_online_image_urls(
                                    list(bad_picks_for_each_pos.values())[sugbanind])
                                target_bad_table[f'Bad Pos {sugbanind+1}'] = lst
                        target_bad_table = pd.DataFrame(target_bad_table)
                        # st.dataframe(target_bad_table)
                        st.markdown(table_with_images(df=target_bad_table, url_columns=[f'Bad Pos {sugbanind+1}' for sugbanind in not_picked_inds]), unsafe_allow_html=True)

    # ----------------- BAN  LIST --------------------------------
    if 'the_bp_node' in st.session_state:
        cur_a_pick_num = 5 - st.session_state.the_bp_node.ally_heros.count(None)       
        cur_o_pick_num = 5 - st.session_state.the_bp_node.opponent_heros.count(None)   
        # cur_round = st.session_state.the_bp_node.cur_round
         
    
    if "suggest_header_placeholder" in st.session_state:
        st.subheader("Ban List")
        bancols = st.columns(2)
        if cur_a_pick_num in [0, 2, 3, 5]:
            with bancols[0]:
                st.multiselect("Input Banned Heroes",
                            options=st.session_state['name_abbrev_dict_keys_list'],
                            format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                            key="ban_multiselect", placeholder="Ban a hero",
                            on_change=update_ban_hero_multiselect)

    # -----------------------------------------------------------
    # --------------- Pick -------------------------------
    if "ally_name_list" in st.session_state:
        ally_name_list = st.session_state.ally_name_list
        st.subheader("Pick List")
        ally_pick_column, oppo_pick_column = st.columns([0.5, 0.5])
        if cur_o_pick_num in [0, 2, 4]:   
            with ally_pick_column:
                ally_hero_display_cols = st.columns(5)
                for ally_ind in range(len(ally_hero_display_cols)):
                    with ally_hero_display_cols[ally_ind]:
                        st.selectbox(f"Ally {ally_name_list[ally_ind]}",
                                    options=st.session_state['name_abbrev_dict_keys_list'],
                                    format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                                    index=None,
                                    key=f"hero_pick_selectbox_{ally_name_list[ally_ind]}",
                                    on_change=ally_pick_select, args=(f"hero_pick_selectbox_{ally_name_list[ally_ind]}", ally_ind))
        
        if cur_a_pick_num in [2,4,5]:
            with oppo_pick_column:
                # multiselect box for selecting oppo because we dont know their pos
                st.multiselect("Input Opponent Heroes",
                            options=st.session_state['name_abbrev_dict_keys_list'],
                            format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                            key="oppo_multiselect", placeholder="Pick opponent heroes",
                            on_change=update_pick_hero_oppo_multiselect)

            

    # ------------ Display ---------------------
        st.subheader("Display")
        ally_pick_column_dis, oppo_pick_column_dis = st.columns([0.5, 0.5])
        with ally_pick_column_dis:
            ally_hero_display_cols = st.columns(5)
            for ally_ind in range(len(ally_hero_display_cols)):
                with ally_hero_display_cols[ally_ind]:
                    with st.expander(f"A {ally_name_list[ally_ind]}", expanded=True):
                        st.empty()
                        target_hero_in_node = st.session_state.the_bp_node.ally_heros[ally_ind]
                        if target_hero_in_node is not None:
                            imgfilenames = [st.session_state['raw_df']
                                            ['Image filename'].loc[target_hero_in_node].strip()]
                            img = get_image_data(imgfilenames)
                            st.image(img, caption=target_hero_in_node,
                                        use_column_width="always")
                            
        with oppo_pick_column_dis:
            oppo_name_list = [" ".join(x.split(" ")[:2])
                              for x in pos_description]
            oppo_hero_display_cols = st.columns(5)
            for oppo_ind in range(len(oppo_hero_display_cols)):
                with oppo_hero_display_cols[oppo_ind]:
                    with st.expander(f"O {oppo_name_list[oppo_ind]}", expanded=True):
                        st.empty()
                        target_hero_in_node = st.session_state.the_bp_node.opponent_heros[oppo_ind]
                        if target_hero_in_node is not None:
                            imgfilenames = [st.session_state['raw_df']
                                            ['Image filename'].loc[target_hero_in_node].strip()]
                            img = get_image_data(imgfilenames)
                            st.image(img, caption=target_hero_in_node,
                                     use_column_width="always")
        
        with st.expander("Ban List Display", expanded=True):
            st.empty()
            row_display_component(
                st.session_state['ban_image_args_list'], 18, show_image_compo)