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
from dota_banpick.st_cache import load_alpha_beta_cache_dict, pos_description, get_hero_csv_data_filtered, get_image_data, get_pos_1_hero_list, get_pos_2_hero_list, get_pos_3_hero_list, get_pos_4_hero_list, get_pos_5_hero_list, get_position_colour_tags, get_position_default_imgspath
from streamlit_option_menu import option_menu
from streamlit_card import card
from annotated_text import annotated_text


image_width = 11


def row_display_component(component_arg_list, width, ):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args)


def show_item_component(img, name):
    st.image(img, caption=name, use_column_width="always")


def pos_card_on_click():
    st.session_state.card_click_count += 1


if __name__ == "__main__":

    st.set_page_config(
        page_title="DOTA2BanPickTool",
        page_icon="✨",
        layout="wide",
    )
    _ = load_alpha_beta_cache_dict()
    st.header("DOTA2 BanPick Tool by Sino-CICI")
    # write a general description about this web app
    st.text("This is a web app for DOTA2 BanPick Tool, you can use it to get some drafting suggestions for DOTA2 games.")
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
    st.header("Common Hero Pools")

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
                    "border-radius": "30px",
                    "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                    "margin": "20px"
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

        imgfilenames = list(tdf['Image filename'].str.strip())
        heronames = list(tdf['Name'].str.strip())
        img_array = get_image_data(imgfilenames)
        args_list = list(zip(img_array, heronames))
        row_display_component(args_list, image_width)
