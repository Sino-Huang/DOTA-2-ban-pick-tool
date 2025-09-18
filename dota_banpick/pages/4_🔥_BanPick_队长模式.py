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
from dota_banpick.alphabeta_captain import alphabeta
from dota_banpick.heuristic import compute_associated_opposite_suggestion_first_round
from dota_banpick.pickaction_captain import StateNodeCaptain
from streamlit_extras.image_in_tables import table_with_images
from dota_banpick.config import DEPTH_LIMIT_CAPTAIN, ALLY_FIRST_ROUND_PICK_CHOICE, UNCOMMON_HEROES, CAPTAIN_BP_ORDER

import pandas as pd
from streamlit.errors import StreamlitAPIException
from dota_banpick.st_cache import load_alpha_beta_cache_dict_captain, record_folder, get_heros, pos_description, get_hero_csv_data_raw, get_name_abbrev_dict, get_hero_csv_data, get_image_data, load_cached_name_hero_pool_dict, load_default_hero_pools, get_chinese_name_data
import subprocess
from subprocess import PIPE
import time

IMAGE_WIDTH = 11
SUGGEST_NUM = 7

def pipe_alphabeta(bpnode, init_depth, alpha, beta, maxplayer, depth_limit, if_use_cache):
    start_time = time.time()
    # subprocess version
    # thein = pickle.dumps(thein)
    # p = subprocess.Popen(["python", "-m", "dota_banpick.alphabeta"],
    #                            stdout=PIPE, stdin=PIPE, stderr=PIPE)
    # stdout_data = p.communicate(input=thein)[0]
    # output = pickle.loads(stdout_data)
    # normal version
    ab_cache_dict = load_alpha_beta_cache_dict_captain()
    # ab_cache_dict = None
    # ! special rule
    # if current cound >= 14, we increase depth limit 
    if bpnode.cur_round >= 14 and bpnode.cur_round <= 17 and depth_limit < 2:
        depth_limit += 0

    if bpnode.cur_round >= 18 and depth_limit < 2:
        depth_limit += 0

    print("Running AlphaBeta with depth limit:", depth_limit)
    print("Calculate for Round:", CAPTAIN_BP_ORDER[bpnode.cur_round])
    output = alphabeta(bpnode, init_depth, alpha, beta, maxplayer, depth_limit, if_use_cache, ab_cache_dict)
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



def form_pick_ban_table(banpick_list, opposite_list, str_pick_choice):
    cols_name = convert_pos_choice_to_readable_lst(str_pick_choice)
    # based on the node's current round, decide the colunn name
    cur_round = st.session_state.the_bp_node.cur_round
    code = CAPTAIN_BP_ORDER[cur_round]
    _, side_code, action_code = code.split(' ')
    # ally_id = st.session_state.the_bp_node.ally_id
    if action_code == 'B':
        last_col_name = "若无法Ban,用这些来克制"
        prefix_name = "🉑Ban"
    else:
        last_col_name = "推荐Ban掉"
        prefix_name = " 🉑Pick"
  

    cols_name.append(last_col_name)
    new_cols_name = [x + prefix_name for x in cols_name[:-1]]
    new_cols_name.append(cols_name[-1])
    cols_name = new_cols_name
    unziplist = list(zip(*banpick_list))
    outputtable = dict()

    for i, lst in enumerate(unziplist):
        # convert lst to image urls
        lst = get_online_image_urls(lst)
        # -----------
        outputtable[cols_name[i]] = lst
    # convert ban_list into chinese names
    updated_ban_list = []
    for sublist in opposite_list:
        updated_sublist = []
        for hero in sublist:
            updated_sublist.append(st.session_state['chinese_name_dict'].get(hero, hero))
        updated_ban_list.append(updated_sublist)
    opposite_list = updated_ban_list
    outputtable[cols_name[-1]] = opposite_list
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
    

def ready_to_bp_on_click():
    # save cache dict ab
    # ab_cache_dict = load_alpha_beta_cache_dict()
    
    ab_cache_dict = None
    if ab_cache_dict is not None:
        with open(os.path.join(record_folder, 'depth_limit_1_warmup_cache_dict_captain.pkl'), 'wb') as f:
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

    
    # remove further table
    tt = 0
    while f"suggest_ban_table_col_{tt}_table" in st.session_state:
        del st.session_state[f"suggest_ban_table_col_{tt}_table"]
        del st.session_state[f"suggest_ban_table_col_{tt}_table_header"]
        tt += 1    

    keylist = list(st.session_state.keys())
    for key in keylist:
        if 'oppo_manual_pos_radio' in key:
            del st.session_state[key]
 
    st.session_state.all_hero_list = get_heros()
    st.session_state.the_bp_node = StateNodeCaptain(
        *st.session_state["ally_hero_pools"], *st.session_state["opponent_hero_pools"], if_bp_first=bool(st.session_state['banpick_order']==0)
    )

    st.session_state['ban_image_args_list'].clear()

    st.session_state.suggest_header_placeholder = "Preparation Drafting Suggestion 初始大数据推荐组合"
    st.session_state.info_placeholder = ("准备阶段，我们针对常见位置组合进行Ban人推荐，如果没有机会Ban掉推荐的英雄，可以考虑在后面选择克制的英雄")
    with st.spinner("AI Searching..."):
        val, prepare_phase_ban_or_pick_dict = pipe_alphabeta(
            st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT_CAPTAIN, True)
    prepare_phase_suggested_opposite_dict = compute_associated_opposite_suggestion_first_round(
        prepare_phase_ban_or_pick_dict)

    

    for ind, comboname in enumerate(prepare_phase_ban_or_pick_dict):
        impacted_player_lst = get_impacted_player_from_choice(
            comboname)
        if len(impacted_player_lst) > 0:
            st.session_state[
                f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname} for {' and '.join(impacted_player_lst)}"
        else:
            st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname}"

        focus_list = [
            x for x, _ in prepare_phase_ban_or_pick_dict[comboname]]
        focus_list, focus_list_inds = get_diverse_suggest_lst(focus_list, SUGGEST_NUM)

        opposite_list = [
                    x for x in prepare_phase_suggested_opposite_dict[comboname]]
        opposite_list = [opposite_list[x] for x in focus_list_inds]
        pick_ban_table = form_pick_ban_table(
            focus_list, opposite_list, comboname)
        st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table


# ! Main Function to update ban hero multiselect
def update_ban_hero_multiselect():

    # in case no change
    banlist = st.session_state["ban_multiselect"]
    if "the_bp_node" in st.session_state:
        banlst_num_before = len(st.session_state.the_bp_node.ban_lst)
        for banhero in banlist:
            st.session_state.the_bp_node.ban_hero(banhero)
        banlst_num_after = len(st.session_state.the_bp_node.ban_lst)
        if banlst_num_before == banlst_num_after:
            return
    
    # * handle images 
    imgfilenames = list(
        st.session_state['raw_df']['Image filename'].loc[list(st.session_state.the_bp_node.ban_lst)].str.strip())
    img_array = get_image_data(imgfilenames)
    st.session_state['ban_image_args_list'] = list(
        zip(img_array, [None for _ in range(len(list(st.session_state.the_bp_node.ban_lst)))]))
    # * --- end handle images

    if st.session_state.the_bp_node.cur_round >= len(CAPTAIN_BP_ORDER):
        return # means we have finished all the rounds

    _, side_code, action_code = CAPTAIN_BP_ORDER[st.session_state.the_bp_node.cur_round].split(' ')

    if side_code == st.session_state.the_bp_node.ally_id:
        # update placeholder stuffs
        # case: we are at ban phase and our ban phase
        with st.spinner("AI Searching..."):
            val, prepare_phase_ban_or_pick_dict = pipe_alphabeta(
                st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT_CAPTAIN, True)
        prepare_phase_suggested_opposite_dict = compute_associated_opposite_suggestion_first_round(
            prepare_phase_ban_or_pick_dict)

        for ind, comboname in enumerate(prepare_phase_ban_or_pick_dict):
            impacted_player_lst = get_impacted_player_from_choice(
                comboname)
            if len(impacted_player_lst) > 0:
                st.session_state[
                    f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname} for {' and '.join(impacted_player_lst)}"
            else:
                st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname}"

            focus_list = [
                x for x, _ in prepare_phase_ban_or_pick_dict[comboname]]
            focus_list, focus_list_inds = get_diverse_suggest_lst(focus_list, SUGGEST_NUM)

            opposite_list = [
                        x for x in prepare_phase_suggested_opposite_dict[comboname]]
            opposite_list = [opposite_list[x] for x in focus_list_inds]
            pick_ban_table = form_pick_ban_table(
                focus_list, opposite_list, comboname)
            st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table


        # remove further table
        while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
            ind += 1


# ! Main Function to update pick hero multiselect
def update_pick_hero_oppo_multiselect():
    oppopicklist = st.session_state['oppo_multiselect']
    # filter ban list, which including selected unavailable ones
    oppopicklist = [
        x for x in oppopicklist if x not in st.session_state.the_bp_node.ban_lst]
    nonecount_before = st.session_state.the_bp_node.opponent_heros.count(None)
    for opohero in oppopicklist:
        st.session_state.the_bp_node.add_hero(opohero, False, -1)
        nonecount = st.session_state.the_bp_node.opponent_heros.count(None)

        header_str = f"对方已选 {len(oppopicklist)} 个英雄"
        st.session_state.suggest_header_placeholder = header_str
      
        st.session_state.info_placeholder = (
            "尝试克制对方英雄，并且避免我方英雄被克制")
        
        if st.session_state.the_bp_node.cur_round >= len(CAPTAIN_BP_ORDER):
            return # means we have finished all the rounds

        # case: if now the round is ours 
        _, side_code, action_code = CAPTAIN_BP_ORDER[st.session_state.the_bp_node.cur_round].split(' ')
        if side_code == st.session_state.the_bp_node.ally_id:
            with st.spinner("AI Searching..."):
                val, prepare_phase_ban_or_pick_dict = pipe_alphabeta(
                    st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT_CAPTAIN, True)
            prepare_phase_suggested_opposite_dict = compute_associated_opposite_suggestion_first_round(
                prepare_phase_ban_or_pick_dict)

            for ind, comboname in enumerate(prepare_phase_ban_or_pick_dict):
                impacted_player_lst = get_impacted_player_from_choice(
                    comboname)
                if len(impacted_player_lst) > 0:
                    st.session_state[
                        f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname} for {' and '.join(impacted_player_lst)}"
                else:
                    st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname}"

                focus_list = [
                    x for x, _ in prepare_phase_ban_or_pick_dict[comboname]]
                focus_list, focus_list_inds = get_diverse_suggest_lst(focus_list, SUGGEST_NUM)

                opposite_list = [
                            x for x in prepare_phase_suggested_opposite_dict[comboname]]
                opposite_list = [opposite_list[x] for x in focus_list_inds]
                pick_ban_table = form_pick_ban_table(
                    focus_list, opposite_list, comboname)
                st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table

            # remove further table
            while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
                del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
                ind += 1

# ! Main Function to update ally pick hero selectbox
def ally_pick_select(select_key, ally_ind):
    selectedhero = st.session_state[select_key]
    st.session_state.suggest_header_placeholder = "如若遇到Bug, 按 (F5) 从头开始"
    
    st.session_state.the_bp_node.add_hero(
        selectedhero, True, ally_ind+1)
    
    if st.session_state.the_bp_node.cur_round >= len(CAPTAIN_BP_ORDER):
        return # means we have finished all the rounds
    
    _, side_code, action_code = CAPTAIN_BP_ORDER[st.session_state.the_bp_node.cur_round].split(' ')
    if side_code == st.session_state.the_bp_node.ally_id:
        st.session_state.info_placeholder = ('我方行动')
    else:
        st.session_state.info_placeholder = ('对方行动')
    
    if side_code == st.session_state.the_bp_node.ally_id:
        with st.spinner("AI Searching..."):
            val, prepare_phase_ban_or_pick_dict = pipe_alphabeta(
                st.session_state.the_bp_node, 0, -999, 999, True, DEPTH_LIMIT_CAPTAIN, True)
        prepare_phase_suggested_opposite_dict = compute_associated_opposite_suggestion_first_round(
            prepare_phase_ban_or_pick_dict)

        for ind, comboname in enumerate(prepare_phase_ban_or_pick_dict):
            impacted_player_lst = get_impacted_player_from_choice(
                comboname)
            if len(impacted_player_lst) > 0:
                st.session_state[
                    f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname} for {' and '.join(impacted_player_lst)}"
            else:
                st.session_state[f"suggest_ban_table_col_{ind}_table_header"] = f"位置组合 {comboname}"

            focus_list = [
                x for x, _ in prepare_phase_ban_or_pick_dict[comboname]]
            focus_list, focus_list_inds = get_diverse_suggest_lst(focus_list, SUGGEST_NUM)

            opposite_list = [
                        x for x in prepare_phase_suggested_opposite_dict[comboname]]
            opposite_list = [opposite_list[x] for x in focus_list_inds]
            pick_ban_table = form_pick_ban_table(
                focus_list, opposite_list, comboname)
            st.session_state[f"suggest_ban_table_col_{ind}_table"] = pick_ban_table
        # remove further table
        while f"suggest_ban_table_col_{ind+1}_table" in st.session_state:
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table"]
            del st.session_state[f"suggest_ban_table_col_{ind+1}_table_header"]
            ind += 1

def manual_change_oppo_pos(hero_name, key):
    # find the pos_ind of that hero
    curr_pos_ind = st.session_state.the_bp_node.opponent_heros.index(hero_name)
    want_pos_ind = int(st.session_state[key].split(' ')[-1]) - 1
    if curr_pos_ind != want_pos_ind:
        # call reset_hero_position
        st.session_state.the_bp_node.reset_hero_position(
            curr_pos_ind, want_pos_ind, is_ally=False)


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

    if 'chinese_name_dict' not in st.session_state:
        chinese_name_df = get_chinese_name_data()
        name_chinese_dict = dict(
            zip(chinese_name_df['Name'], chinese_name_df['Chinese Name']))
        st.session_state['chinese_name_dict'] = name_chinese_dict

    ready_to_bp = False
    st.title("BP模拟 - 队长模式")
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
                "未发现英雄池数据，启用预设英雄池，可去Edit Hero Pool页面添加数据。")
        else:
            # show the player and ask to select position
            plyername_arg_list = [(playername,)
                                  for playername in player_cache_dict]
            row_display_component(plyername_arg_list, 2,
                                  show_player_selectoption)

        with st.expander("Team info", expanded=True):
            st.table(st.session_state['available_positions'])

        # create a binary slider for either bp first or bp second

        who_pick_first = st.radio(
            "BP顺序", ['先手','后手'], captions=["先Ban先选", "后Ban后选"],
        )
        if who_pick_first == '先手':
            st.session_state['banpick_order'] = 0 # 0 means first ban and pick
        else:
            st.session_state['banpick_order'] = 1 # 1 means second ban and pick
        st.markdown(f"为{'先手' if st.session_state['banpick_order'] == 0 else '后手'}方提供建议")


        confirmteambut = st.button(
            "开始BP", type="primary", use_container_width=True, on_click=ready_to_bp_on_click)


    if 'the_bp_node' not in st.session_state:
        # add instruction 

        st.markdown("""
## DOTA2 队长模式BP模拟器使用指南
### 一、前期准备（侧边栏操作）
1. **分配玩家与位置**：侧边栏会显示缓存的玩家列表，为每位玩家选择对应位置（如“1号位 Carry”），系统会自动加载该玩家的英雄池。
2. **选择BP顺序**：在“BP顺序”处选择“先手”（先Ban先选）或“后手”（后Ban后选），系统会基于所选顺序提供建议。
3. **启动BP**：确认配置后，点击“开始BP”按钮，进入BP阶段。


### 二、BP阶段核心操作
#### 1. 查看当前状态
- 页面会显示**当前轮次**（如“第1轮，我方Ban人”）和**下一步操作**，明确当前该谁进行Ban/Pick。
- 顶部表格会展示AI生成的位置组合建议（如“位置组合 [1,2]”），包含推荐Ban/Pick的英雄及克制英雄。

#### 2. Ban人操作
- 当轮次提示“我方Ban人”时，在“请选择要Ban英雄”下拉框中，勾选想要Ban的英雄，系统会自动更新Ban列表并刷新AI建议。
- 已Ban英雄会在“已Ban英雄池”中分类展示（我方Ban/对方Ban），方便查看禁用记录。

#### 3. Pick人操作
- **我方Pick**：当轮次提示“我方选人”时，在“Ally 1号位/2号位...”对应的下拉框中，为每个位置选择英雄，选择后会在“Display”区域显示已选英雄。
- **模拟对方Pick**：当轮次提示“对方选人”时，在“模拟输入对方已选英雄”下拉框中，勾选对方可能选择的英雄，系统会基于此更新克制建议。


### 三、关键提示
1. 若英雄池数据缺失，系统会启用预设英雄池，可后续在“Edit Hero Pool”页面补充玩家英雄池数据。
2. 若遇到界面异常，按键盘“F5”刷新页面，重新从“前期准备”步骤开始即可。
3. AI建议表格中，“🉑Ban/🉑Pick”列展示推荐英雄（带图片），最后一列展示“若无法Ban/推荐Ban掉”的克制英雄（中文名称）。
""")
                    

    # ---------------Table Placeholder -------------------
    if "suggest_header_placeholder" in st.session_state:
        st.subheader(st.session_state.suggest_header_placeholder)
        st.info(st.session_state.info_placeholder)
        with st.container():
            col_ind_c = 0
            while f"suggest_ban_table_col_{col_ind_c}_table" in st.session_state:
                col_ind_c += 1
            st.info(f"共 {col_ind_c} 种位置组合建议")
            combocols = st.columns(col_ind_c, gap="small")
            for ind in range(col_ind_c):
                with combocols[ind]:
                    st.info(
                        st.session_state[f"suggest_ban_table_col_{ind}_table_header"])
                    target_table = pd.DataFrame(
                        st.session_state[f"suggest_ban_table_col_{ind}_table"])
                    # st.dataframe(target_table)

                    target_table_keys = list(target_table.keys())
                    target_table_keys_len = len(target_table_keys)

                    image_col_config = dict()
                    for key in target_table_keys[:-1]:
                        image_col_config[key] = st.column_config.ImageColumn(
                            key, help="Image loaded from a URL"
                        )

                    st.dataframe(
                        target_table,
                        column_config=image_col_config,
                        hide_index=True,
                    )

                    # st.markdown(table_with_images(df=target_table, url_columns=target_table_keys[:target_table_keys_len-1]), unsafe_allow_html=True)

   

    # --------------- Auxiliary Info -------------------
    if 'the_bp_node' in st.session_state:
        cur_a_pick_num = 5 - st.session_state.the_bp_node.ally_heros.count(None)       
        cur_o_pick_num = 5 - st.session_state.the_bp_node.opponent_heros.count(None)   
        cur_round = st.session_state.the_bp_node.cur_round
        if cur_round >= 0 and cur_round < len(CAPTAIN_BP_ORDER):
            order_code = CAPTAIN_BP_ORDER[cur_round]
            next_order_code = CAPTAIN_BP_ORDER[cur_round + 1] if cur_round + 1 < len(CAPTAIN_BP_ORDER) else None
            code_round, code_side, code_bp = order_code.split(" ")
            if code_side == 'A':
                code_side = 0 
            else:
                code_side = 1
            if code_bp == 'B':
                code_bp = 'Ban人'
            else:
                code_bp = 'Pick人'
            if next_order_code is not None:
                next_code_round, next_code_side, next_code_bp = next_order_code.split(" ")
                if next_code_side == 'A':
                    next_code_side = 0 
                else:
                    next_code_side = 1
                if next_code_bp == 'B':
                    next_code_bp = 'Ban人'
                else:
                    next_code_bp = 'Pick人'
            info_str = f"当前为第 {code_round} 轮, {'我方' if code_side == 0 else '对方'} {code_bp}"
            if next_order_code is not None:
                info_str += f", 下一步为 {'我方' if next_code_side == 0 else '对方'} {next_code_bp}"
            st.warning(info_str)
            # actually we can update title here
            code_round, code_side, code_bp = CAPTAIN_BP_ORDER[st.session_state.the_bp_node.cur_round].split(" ")
            if st.session_state.the_bp_node.ally_id == code_side:
                if code_bp == 'B':
                    st.subheader(f"第{code_round}轮，我方Ban人")
                else:
                    st.subheader(f"第{code_round}轮，我方选人")
            else:
                if code_bp == 'B':
                    st.subheader(f"第{code_round}轮，对方Ban人")
                else:
                    st.subheader(f"第{code_round}轮，对方选人")
    
    # ----------------- BAN  LIST --------------------------------

    if "suggest_header_placeholder" in st.session_state:
        if 'order_code' in locals():
            code_round, code_side, code_bp = order_code.split(" ")
            if code_bp == 'B':
                st.subheader("（激活）请在此处Ban英雄")
            
            bancols = st.columns(2)
            if code_bp == 'B':
                with bancols[0]:
                    st.multiselect("请选择要Ban英雄",
                                options=st.session_state['name_abbrev_dict_keys_list'],
                                format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                                key="ban_multiselect", placeholder="Ban a hero",
                                on_change=update_ban_hero_multiselect)

    # -----------------------------------------------------------
    # --------------- Pick -------------------------------
    if "ally_name_list" in st.session_state:
        ally_name_list = st.session_state.ally_name_list
        if 'order_code' in locals():
            code_round, code_side, code_bp = order_code.split(" ")
            ally_pick_column, oppo_pick_column = st.columns([0.5, 0.5])
            if code_bp == 'P' and code_side == st.session_state.the_bp_node.ally_id:
                ally_pick_activated = True
            else:
                ally_pick_activated = False
            if not ally_pick_activated:
                st.subheader("已选英雄")
            else:
                st.subheader("（激活）请选择我方英雄")
            if ally_pick_activated:   
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
            
            if code_bp == 'P' and code_side == st.session_state.the_bp_node.opponent_id:
                # it means opponent is picking now
                with oppo_pick_column:
                    # multiselect box for selecting oppo because we dont know their pos
                    st.multiselect("（激活）模拟输入对方已选英雄",
                                options=st.session_state['name_abbrev_dict_keys_list'],
                                format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                                key="oppo_multiselect", placeholder="Pick opponent heroes",
                                on_change=update_pick_hero_oppo_multiselect)

            with oppo_pick_column:
                # add manual set hero position for opponent (given that currently we just guess their pos, but we can manually set them)
                with st.expander("手动设置对方英雄位置", expanded=False):
                    manual_oppo_pos_cols = st.columns(5)
                    for col_ix, hero_name in enumerate(st.session_state.the_bp_node.sorted_opponent_heros):
                        pos_ind = st.session_state.the_bp_node.opponent_heros.index(hero_name)
                        with manual_oppo_pos_cols[col_ix]:
                            oppo_manual_pos_radio = st.radio(
                                    hero_name,
                                    ['Pos 1', 'Pos 2', 'Pos 3', 'Pos 4', 'Pos 5'],
                                    index=pos_ind,
                                    key=f'{hero_name}_oppo_manual_pos_radio_special_key',
                                    on_change=manual_change_oppo_pos,
                                    args=(hero_name, f'{hero_name}_oppo_manual_pos_radio_special_key')
                                )
                        


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
        
        with st.expander("已Ban英雄池", expanded=True):
            st.empty()
            # split st.session_state['ban_image_args_list'] into 2 columns, one is ally ban, the other is oppo ban
            if len(st.session_state['ban_image_args_list']) > 0:
                ally_Ban_lst = [] 
                oppo_Ban_lst = [] 
                b_count = 0 
                for ind, bp_code in enumerate(CAPTAIN_BP_ORDER):
                    if b_count >= len(st.session_state['ban_image_args_list']):
                        break
                    _, side_code, action_code = bp_code.split(' ')
                    if action_code == 'B':
                        if side_code == st.session_state.the_bp_node.ally_id:
                            ally_Ban_lst.append(st.session_state['ban_image_args_list'][b_count])
                        else:
                            oppo_Ban_lst.append(st.session_state['ban_image_args_list'][b_count])
                        b_count += 1

                ban_display_cols = st.columns(2)
                if len(ally_Ban_lst)> 0: 
                    with ban_display_cols[0]:
                        st.text("我方Ban人")
                        row_display_component(
                            ally_Ban_lst, 18, show_image_compo)
                if len(oppo_Ban_lst) > 0:
                    with ban_display_cols[1]:
                        st.text("对方Ban人")
                        row_display_component(
                            oppo_Ban_lst, 18, show_image_compo)