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
from dota_banpick.heuristic import compute_bad_picks_for_each_pos
from dota_banpick.pickaction import StateNode
from dota_banpick.config import DEPTH_LIMIT
import pandas as pd

from dota_banpick.st_cache import get_hero_csv_data, get_image_data, init_warmup_cache_dict, load_cached_name_hero_pool_dict, load_default_hero_pools

def row_display_component(component_arg_list, width):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args)
    
def show_item_component(img, name):
    col1, col2 = st.columns(2)
    with col1:
        st.image(img)
        st.markdown(f'<p class="small-font">{name}</p>', unsafe_allow_html=True)
    with col2:
        st.text_input("status", label_visibility="hidden", max_chars = 2, 
                    key=f"bpinput_{name}", on_change=inp_on_change, args=(f"bpinput_{name}", name))
            
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

image_width = 11 


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

    cache_dict = load_cached_name_hero_pool_dict()
    alpha_beta_cache_dict = init_warmup_cache_dict()
    if "ally_player_names" not in cache_dict:
        st.warning("You do not have available hero pool, please create one first.")
    else:
        st.session_state["ally_player_names"] = cache_dict["ally_player_names"]
        st.session_state["ally_hero_pools"] = cache_dict["ally_hero_pools"]
        
        if 'banpicknode' not in st.session_state:   
            st.session_state.banpicknode = StateNode(*st.session_state["ally_hero_pools"], *st.session_state["opponent_hero_pools"])


        
    st.markdown(f"""# BP Round {st.session_state.banpicknode.cur_round}""")

    reset_but = st.button("Reset BP")
    if reset_but:
        st.session_state.banpicknode = StateNode(*st.session_state["ally_hero_pools"], *st.session_state["opponent_hero_pools"])
    ac_but = st.button("Ask For Suggestions")
    # display 
    st.write(st.session_state.banpicknode)
    st.write("Banned")
    st.write(st.session_state.banpicknode.ban_lst)

    if ac_but:
        oppo_hero_list = [
            st.session_state.banpicknode.opponent_pos_1_hero,
            st.session_state.banpicknode.opponent_pos_2_hero,
            st.session_state.banpicknode.opponent_pos_3_hero,
            st.session_state.banpicknode.opponent_pos_4_hero,
            st.session_state.banpicknode.opponent_pos_5_hero,
        ]
        oppo_hero_list = [x for x in oppo_hero_list if x is not None]
        
        if st.session_state.banpicknode.cur_round == 0:
            _, suggested_hero_pick_dict = alphabeta(
            st.session_state.banpicknode, 0, -999, 999, True, 1, init_warmup_cache_dict())
            st.write("Suggest")
            cols = st.columns(len(suggested_hero_pick_dict))
            for i, k in enumerate(suggested_hero_pick_dict):
                with cols[i]:
                    st.write(f"Pos {k}")
                    st.write([str(x[0]) for x in suggested_hero_pick_dict[k]][:4])
                

                
        elif st.session_state.banpicknode.cur_round >= 2 and len(oppo_hero_list) >= 2:
            _, suggested_hero_pick_dict = alphabeta(
            st.session_state.banpicknode, 0, -999, 999, True, 1, None)
            bad_hero_eles = compute_bad_picks_for_each_pos(st.session_state.banpicknode)
            
            st.write("Suggest")
            cols = st.columns(len(suggested_hero_pick_dict))
            for i, k in enumerate(suggested_hero_pick_dict):
                with cols[i]:
                    st.write(f"Pos {k}")
                    st.write([str(x[0]) for x in suggested_hero_pick_dict[k]][:4])


            st.write("Not Good")
            cols = st.columns(len(bad_hero_eles))
            for i, k in enumerate(bad_hero_eles):
                with cols[i]:
                    st.write(f"Pos {k}")
                    st.write(bad_hero_eles[k])

    for t in ["Strength", "Agility", "Intelligence", "Universal"]:
        with st.container():
            st.markdown(f"""#### {t}""")
            df = get_hero_csv_data(t)
            # st.dataframe(df)
            imgfilenames = list(df['Image filename'].str.strip())
            heronames = list(df['Name'].str.strip())
            img_array = get_image_data(imgfilenames)
            args_list = list(zip(img_array, heronames))
            row_display_component(args_list, image_width)