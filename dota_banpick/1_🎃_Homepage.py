from functools import partial
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
from dota_banpick.config import DEPTH_LIMIT, LAST_UPDATE
from dota_banpick.heuristic import compute_with_and_counter_heroes_for_each_pos
from dota_banpick.st_cache import get_hero_csv_data_raw, get_online_image_urls, hero_counter_row_display_component, pos_description, load_today_hero_winrate_dict, get_hero_csv_data_filtered, get_image_data, get_pos_1_hero_list, get_pos_2_hero_list, get_pos_3_hero_list, get_pos_4_hero_list, get_pos_5_hero_list, get_position_colour_tags, get_position_default_imgspath
from streamlit_option_menu import option_menu
from streamlit_card import card
from annotated_text import annotated_text
from streamlit_extras.image_in_tables import table_with_images
import numpy as np
from streamlit_js_eval import streamlit_js_eval

normal_image_width_mobile = 5
show_cntr_image_width_mobile = 1
normal_image_width_pc = 11
show_cntr_image_width_pc = 3

def row_display_component(component_arg_list, width, position):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args, position)

def show_item_component(img, name, winrate, position, suggest_num = 3):
    if st.session_state['if_show_counter']:
        captionname = f"wr:{winrate}"
    else:
        captionname = name+f" wr:{winrate}"
    if st.session_state['screen_width'] < 800:
        st.image(img, caption=captionname, use_column_width="always")
    else:
        st.image(img, caption=captionname, width=100)
    if 'if_show_counter' in st.session_state:
        if st.session_state['if_show_counter']:
            _, counter_dict, _ = compute_with_and_counter_heroes_for_each_pos(
                [name], suggest_num)
            if position == 1:
                targ_positions = [3,4,2,1]
            elif position == 2:
                targ_positions = [2,3,1,4]
            elif position == 3:
                targ_positions = [1,5,2,4]
            elif position == 4:
                targ_positions = [1,2,3,4]
            elif position == 5:
                targ_positions = [1,2,3,4]
            dataframe = {
                        f"Pos {targ_position} CNTR": get_online_image_urls(counter_dict[targ_position]) for targ_position in targ_positions
                        }
            dataframe = pd.DataFrame(dataframe)
            st.caption(f"Counters for {name}")
            st.markdown(table_with_images(df=dataframe,
                                          url_columns=[f"Pos {targ_position} CNTR" for targ_position in targ_positions],),
                        unsafe_allow_html=True)
            st.divider()


def pos_card_on_click():
    st.session_state.card_click_count += 1


if __name__ == "__main__":

    st.set_page_config(
        page_title="DOTA2 Ban Pick Tool",
        page_icon="✨",
        layout="wide",
    )
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
    st.header("Hero Pools with Live Stats!")
    st.toggle("Show Counter Heroes", key="if_show_counter")

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
            if st.session_state['if_show_counter']:
                row_display_component(args_list, show_cntr_image_width_mobile, st.session_state['show_pos_hero_ind'] + 1)
            else:
                row_display_component(args_list, normal_image_width_mobile, st.session_state['show_pos_hero_ind'] + 1)
        else:
            if st.session_state['if_show_counter']:
                row_display_component(args_list, show_cntr_image_width_pc, st.session_state['show_pos_hero_ind'] + 1)
            else:
                row_display_component(args_list, normal_image_width_pc, st.session_state['show_pos_hero_ind'] + 1)
