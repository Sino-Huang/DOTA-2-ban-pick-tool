from functools import partial
import streamlit as st
from glob import glob
import json
import os
from natsort import natsorted
import streamlit as st
from streamlit.errors import StreamlitAPIException
from multiprocessing import Manager
import copy
import pandas as pd
import pickle
from dota_banpick.config import DEPTH_LIMIT, LAST_UPDATE
from dota_banpick.heuristic import compute_with_and_counter_heroes_for_each_pos
from dota_banpick.st_cache import get_hero_csv_data_raw, get_online_image_urls, hero_counter_row_display_component, load_winlane_hero_dict, pos_description, load_today_hero_winrate_dict, get_hero_csv_data_filtered, get_image_data, get_pos_1_hero_list, get_pos_2_hero_list, get_pos_3_hero_list, get_pos_4_hero_list, get_pos_5_hero_list, get_position_colour_tags, get_position_default_imgspath
from streamlit_option_menu import option_menu
from streamlit_card import card
from annotated_text import annotated_text
from streamlit_extras.image_in_tables import table_with_images
import numpy as np
from streamlit_js_eval import streamlit_js_eval

normal_image_width_mobile = 2
show_cntr_image_width_mobile = 2
normal_image_width_pc = 6
show_cntr_image_width_pc = 4

def row_display_component(component_arg_list, width, position):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args, position)

def show_item_component(img, name, winrate, position, suggest_num = 5):
    with st.expander(f"{name}", expanded=False if st.session_state['screen_width'] < 800 and st.session_state['if_show_counter'] in ["Win Lane", "Win Game"] else True):
        if st.session_state['if_show_counter']:
            captionname = f"wr:{winrate}"
        else:
            captionname = name+f" wr:{winrate}"
        if st.session_state['screen_width'] < 800:
            st.image(img, caption=captionname, width=80)
        else:
            st.image(img, caption=captionname, width=100)
            
        if 'if_show_counter' in st.session_state:
            if st.session_state['if_show_counter'] in ["Win Lane", "Win Game"]:
                if position == 1:
                    versus_filter_list = get_pos_3_hero_list() + get_pos_4_hero_list()
                    with_filter_list = get_pos_5_hero_list()
                    with_pos = 5 
                    versus_poses = [3,4]
                elif position == 2:
                    versus_filter_list = get_pos_2_hero_list()
                    with_filter_list = [] # no with for pos 2
                    with_pos = -1 
                    versus_poses = [2]
                elif position == 3:
                    versus_filter_list = get_pos_1_hero_list() + get_pos_5_hero_list()
                    with_filter_list = get_pos_4_hero_list()
                    with_pos = 4
                    versus_poses = [1,5]
                elif position == 4:
                    versus_filter_list = get_pos_1_hero_list() + get_pos_5_hero_list()
                    with_filter_list = get_pos_3_hero_list()
                    with_pos = 3
                    versus_poses = [1,5]
                    
                elif position == 5:
                    versus_filter_list = get_pos_3_hero_list() + get_pos_4_hero_list()
                    with_filter_list = get_pos_1_hero_list()
                    with_pos = 1
                    versus_poses = [3,4]
                    
                if st.session_state['if_show_counter'] == "Win Lane":
                    with_list = list(st.session_state["hero_lanewin_with_dict"][name].keys())
                    with_list = [n for n in with_list if n in with_filter_list][:suggest_num]
                    versus_list = list(st.session_state["hero_lanewin_versus_dict"][name].keys())
                    versus_list = [n for n in versus_list if n in versus_filter_list][:suggest_num]
                    caption_str = f" Win Lane Advice"
                    
                elif st.session_state['if_show_counter'] == "Win Game":
                    with_dict, counter_dict, bad_counter_dict = compute_with_and_counter_heroes_for_each_pos(
                        [name], suggest_num)
                    if with_pos == -1:
                        with_list = []
                    else:
                        with_list = with_dict[with_pos]
                    versus_pos_len = len(versus_poses)
                    first_ele_size = suggest_num // versus_pos_len + suggest_num % versus_pos_len
                    other_ele_size = suggest_num // versus_pos_len
                    versus_list = []
                    for i, pos in enumerate(versus_poses):
                        if i == 0:
                            versus_list += counter_dict[pos][:first_ele_size]
                        else:
                            versus_list += counter_dict[pos][:other_ele_size]
                    
                    caption_str = f" Win Game Advice"
                if len(with_list) == suggest_num and position != 2:
                    if st.session_state['screen_width'] < 800:
                        dataframe_c = {
                                    f"CNTR": get_online_image_urls(versus_list),
                                    }
                    
                        dataframe_c = pd.DataFrame(dataframe_c)
                        dataframe_w = {
                                    f"WITH": get_online_image_urls(with_list),
                                    }
                    
                        dataframe_w = pd.DataFrame(dataframe_w)
                        st.caption(caption_str)
                        st.markdown(table_with_images(df=dataframe_c,
                                                    url_columns=["CNTR",],),
                                    unsafe_allow_html=True)
                        st.markdown(table_with_images(df=dataframe_w,
                                                    url_columns=["WITH",],),
                                    unsafe_allow_html=True)
                    else:
                        dataframe = {
                                    f"CNTR": get_online_image_urls(versus_list),
                                    f"WITH": get_online_image_urls(with_list),
                                    }
                    
                        dataframe = pd.DataFrame(dataframe)
                        st.caption(caption_str)
                        st.markdown(table_with_images(df=dataframe,
                                                    url_columns=["CNTR", "WITH"],),
                                    unsafe_allow_html=True)
                else:
                    dataframe = {
                                f"CNTR": get_online_image_urls(versus_list),
                                }
          
                    dataframe = pd.DataFrame(dataframe)
                    st.caption(caption_str)
                    st.markdown(table_with_images(df=dataframe,
                                                url_columns=["CNTR",],),
                                unsafe_allow_html=True)


def pos_card_on_click():
    st.session_state.card_click_count += 1


if __name__ == "__main__":
    try:
        st.set_page_config(
            page_title="DOTA2 Ban Pick Tool",
            page_icon="✨",
            layout="wide",
        )
    except StreamlitAPIException:
        pass
    # _ = load_alpha_beta_cache_dict()
    st.header("DOTA2 Ban Pick Tool by Sino-CICI")
    # write a general description about this web app
    st.text("This is a web app for DOTA2 Ban Pick Tool, you can use it to get some drafting suggestions for DOTA2 games.")
    st.text("""Legitimacy and Fair Play Clarification:
No Cheating Involved:
    Our tool is fundamentally different from real-time game-enhancing applications like Overwolf. It does not interact with the DOTA 2 game client or servers during gameplay nor does it parse player information in real-time.
Purely a Drafting Aid:
    This tool is designed to serve as a drafting practice tool. Its sole purpose is to assist players in understanding and strategizing around the drafting phase of the game. It simulates various drafting scenarios to help players make informed decisions on hero selections and bans based on predefined metrics and algorithms.
No Real-Time Assistance:
    The DOTA 2 Ban Pick Tool does not provide any real-time assistance, insights, or advantages during actual gameplay. It operates exclusively outside the game environment, thus preserving the game's competitive integrity.
No Data Parsing:
    Unlike some other tools, our application does not parse or analyze player data during game runtime. It strictly operates based on predefined hero pools and user inputs prior to engaging in a game.
Privacy Respected:
    We highly respect user privacy and game ethics. No personal or game data is accessed, collected, or shared through the use of this tool.""")
    st.markdown("""
<style>
p {
    font-size:1.2em !important;
}
</style>
""", unsafe_allow_html=True)

    if "posoption_menu" not in st.session_state:
        st.session_state["posoption_menu"] = pos_description[0]

    if "card_click_count" not in st.session_state:
        st.session_state.card_click_count = 0

    if "show_pos_hero_ind" not in st.session_state:
        st.session_state["show_pos_hero_ind"] = -1
        
    if "today_winrate_dict" not in st.session_state:
        st.session_state["today_winrate_dict"] = load_today_hero_winrate_dict()
        
    if "hero_lanewin_versus_dict" not in st.session_state:
        st.session_state["hero_lanewin_versus_dict"], st.session_state["hero_lanewin_with_dict"] = load_winlane_hero_dict()
        
    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = get_hero_csv_data_raw()
        
    if "screen_width" not in st.session_state:
        st.session_state["screen_width"] = int(streamlit_js_eval(js_expressions='screen.width', key = 'SCR'))
        
    if st.session_state["screen_width"] < 800:
        st.write('''<style>

[data-testid="column"] {
    width: calc(20.0% - 1rem) !important;
    flex: 1 1 calc(20.0% - 1rem) !important;
    min-width: calc(20.0% - 1rem) !important;
}
</style>''', unsafe_allow_html=True)

    st.warning(f"Last Update: {LAST_UPDATE}")
    card("Start Editing Your Hero Pool", text=("Provide your usual positions → Edit your hero pool → Begin to banpick"),
         url="/Edit_Hero_Pool", on_click=lambda: None,
         image="https://clan.cloudflare.steamstatic.com/images//3703047/4ff438f53339fe12849e788e3902b319d2b0828c.jpg",
         styles={
             "card": {
                 "width": "100%",
                 "height": "300px",
                 "border-radius": "60px",
                 "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                 "margin": "20px"
             },
    })
    st.header("Hero Pools with Live Stats and Win Lane Advice!")
    st.warning("If you are looking for Win Game advice, please check out the Hero Counter page.")
    st.radio("What's your preference for hero advice?", ["Win Lane", "Win Game", "Hide"], captions=["You may not win the game in the end but you can smoothly survive the early game and let others to carry you.", "Calm down and be patient, you can win the game!", "Hide for saving space."], key="if_show_counter", index=2)

    card_cols = st.columns(5, gap="small")

    for ind, col in enumerate(card_cols):
        with col:
            if f'pc_last_true_{ind}' not in st.session_state:
                st.session_state[f'pc_last_true_{ind}'] = ""
            pos_text = " ".join(pos_description[ind].split(" ")[:2])
            pos_desc_text = pos_description[ind].split(" ")[-1]

            card_hasclick = card(pos_desc_text, text=pos_text, image=get_position_default_imgspath()[ind],
                                 styles={
                "card": {
                    "width": "100%",
                    "height": "120px",
                    "border-radius": "5px",
                    "box-shadow": "0 0 1px rgba(0,0,0,0.5)",
                    "margin": "0px"
                }
            }, key=f"pos_card_{ind}_{st.session_state.card_click_count}", on_click=pos_card_on_click)

    for k in st.session_state:
        if "pos_card" in k:
            pind = k.split("_")[-2]
            if st.session_state[k]:
                if k != st.session_state[f'pc_last_true_{pind}']:
                    # means get changed
                    st.session_state[f'pc_last_true_{pind}'] = k
                    st.session_state["show_pos_hero_ind"] = int(pind)
    tdf = None

    if st.session_state["show_pos_hero_ind"] == 0:
        tdf = get_hero_csv_data_filtered(get_pos_1_hero_list())
    elif st.session_state["show_pos_hero_ind"] == 1:
        tdf = get_hero_csv_data_filtered(get_pos_2_hero_list())

    elif st.session_state["show_pos_hero_ind"] == 2:
        tdf = get_hero_csv_data_filtered(get_pos_3_hero_list())

    elif st.session_state["show_pos_hero_ind"] == 3:
        tdf = get_hero_csv_data_filtered(get_pos_4_hero_list())

    elif st.session_state["show_pos_hero_ind"] == 4:
        tdf = get_hero_csv_data_filtered(get_pos_5_hero_list())

    if tdf is not None:
        annotated_text((pos_description[st.session_state["show_pos_hero_ind"]].split(
            " ")[-1], f"pos {st.session_state['show_pos_hero_ind'] + 1}", get_position_colour_tags()[st.session_state['show_pos_hero_ind']]))

        # sort the heroes by winrate
        heronames = list(tdf['Name'].str.strip())
        winrates = [st.session_state["today_winrate_dict"][name]['winrate'] for name in heronames]
        index_sorted = np.argsort(winrates)[::-1]
        winrates = np.array(winrates)[index_sorted]
        # round 2 decimal places
        winrates = [np.round(wr, 2) for wr in winrates]
        
        tdf = tdf.iloc[index_sorted]        
        heronames = list(tdf['Name'].str.strip())
        imgfilenames = list(tdf['Image filename'].str.strip())

        img_array = get_image_data(imgfilenames)
        args_list = list(zip(img_array, heronames, winrates))
        if st.session_state['screen_width'] < 800:
            if st.session_state['if_show_counter'] in ["Win Lane", "Win Game"]:
                row_display_component(args_list, show_cntr_image_width_mobile, st.session_state['show_pos_hero_ind'] + 1)
            else:
                row_display_component(args_list, normal_image_width_mobile, st.session_state['show_pos_hero_ind'] + 1)
        else:
            if st.session_state['if_show_counter'] in ["Win Lane", "Win Game"]:
                row_display_component(args_list, show_cntr_image_width_pc, st.session_state['show_pos_hero_ind'] + 1)
            else:
                row_display_component(args_list, normal_image_width_pc, st.session_state['show_pos_hero_ind'] + 1)
