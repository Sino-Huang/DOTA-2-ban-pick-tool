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

from dota_banpick.st_cache import get_hero_csv_data, get_heros, get_image_data, load_cached_name_hero_pool_dict, load_default_hero_pools





def row_display_component(component_arg_list, width):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args)
    
def show_item_component(img, name, toggle_val):
    st.image(img)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<p class="small-font">{name}</p>', unsafe_allow_html=True)
    with col2:
        st.toggle("activate", label_visibility="collapsed", value=toggle_val, key=f"toggle_{name}")
        

def player_basic_info_callback():
    pos_ind = ['Pos 1 Carry',
                           'Pos 2 Mid',
                           'Pos 3 Offlane',
                           'Pos 4 Ganker',
                           'Pos 5 Support',
                           ].index(st.session_state.form_pos_rad)
    st.session_state["target_hero_pool"] = copy.deepcopy(st.session_state["ally_hero_pools"][pos_ind])
    st.session_state["target_pos"] = pos_ind
    st.session_state["ally_player_names"][pos_ind] = st.session_state.form_playername
    st.session_state['activate_hero_flag'] = True
    st.session_state['activate_basic_info_flag'] = False

    

    
def complete_edit_callback():
    # modify target hero pool
    a_new_hero_list = []
    for hero_name in st.session_state['allheroes']:
        togle_k = f"toggle_{hero_name}"
        if st.session_state[togle_k]:
            a_new_hero_list.append(hero_name)
    st.session_state["target_hero_pool"] = a_new_hero_list
    pos_ind = st.session_state["target_pos"]
    st.session_state["ally_hero_pools"][pos_ind] = a_new_hero_list
    st.session_state['activate_hero_flag'] = False
    st.session_state['display_stats_flag'] = True
    st.session_state['activate_basic_info_flag'] = False
    
    # auto cache
    cache_dict = load_cached_name_hero_pool_dict()
    cache_dict["ally_player_names"] = st.session_state["ally_player_names"]
    cache_dict["ally_hero_pools"] = st.session_state["ally_hero_pools"]
    # display stats 
    st.session_state.data_ready_count += 1
    
def input_user_info_callback():
    st.toast("Start Editing Your Own Hero Pool", icon="🌟")
    st.session_state['activate_hero_flag'] = False
    st.session_state['display_stats_flag'] = False
    st.session_state['activate_basic_info_flag'] = True
    


def load_from_cache_callback():
    st.toast("Load From Cache", icon="📕")
    st.session_state['activate_hero_flag'] = False
    cached_dict = load_cached_name_hero_pool_dict()
    if "ally_player_names" not in cached_dict:
        st.warning(
            "Cached Dict Has No Data, You Shall Try Other Methods!", icon="❤️‍🔥")
    else:
        st.session_state["ally_player_names"] = cached_dict["ally_player_names"]
        st.session_state["ally_hero_pools"] = cached_dict["ally_hero_pools"]
        # display hero pool
        st.session_state['display_stats_flag'] = True
        st.session_state.data_ready_count += 1
    
def file_upload_onchange():
    uploaded_file = st.session_state['uploader_key']
    
    if uploaded_file is not None:
        st.toast("Upload Local Hero Pools", icon="📂")
        heropool_json = uploaded_file.read()
        heropool_json = json.loads(heropool_json)
        uploaded_file = None
        if "ally_player_names" not in heropool_json:
            st.warning(
                "Not A Valid Hero Pools File, You Shall Try Other Methods!", icon="❤️‍🔥")
        else:
            st.session_state["ally_player_names"] = heropool_json["ally_player_names"]
            st.session_state["ally_hero_pools"] = heropool_json["ally_hero_pools"]
            # display hero pool
            st.session_state['display_stats_flag'] = True
            st.session_state.data_ready_count += 1
    



image_width = 11 

if __name__ == "__main__":
    st.set_page_config(
        layout="wide"
    )
    st.session_state.data_ready_count = 0
    if 'activate_hero_flag' not in st.session_state:
        st.session_state['activate_hero_flag'] = False
    if 'activate_basic_info_flag' not in st.session_state:
        st.session_state['activate_basic_info_flag'] = False
        
    if "display_stats_flag" not in st.session_state:
        st.session_state['display_stats_flag'] = False

    st.markdown("""
    <style>
    .small-font {
        font-size:11px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # default

    if "opponent_hero_pools" not in st.session_state:
        st.session_state["opponent_hero_pools"] = load_default_hero_pools()

    if "ally_player_names" not in st.session_state:
        st.session_state["ally_player_names"] = ['Pos 1 Bot',
                                                'Pos 2 Bot',
                                                'Pos 3 Bot',
                                                'Pos 4 Bot',
                                                'Pos 5 Bot'
                                                ]


    if "ally_hero_pools" not in st.session_state:
        st.session_state["ally_hero_pools"] = load_default_hero_pools()
        
    if 'allheroes' not in st.session_state:
        st.session_state["allheroes"] = get_heros()
    st.markdown("""## Edit Hero Pools

    - To run the BanPick tool, you are required to provide your hero pool and your position.""")

    st.markdown(
        """
    <style>
    button {
        height: auto;
        padding-top: 15px !important;
        padding-bottom: 15px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


    col1, col2, col3= st.columns(3)
    with col1:
        start_but = st.button("Edit Your Pool", on_click=input_user_info_callback)
        download_button_placeholder = st.empty()

    with col2:
        ca_but = st.button("Import From Cache", on_click=load_from_cache_callback)

    with col3:
        # ! upload widget need to always display , also remember any button will refresh page when using if
        # ! so far solution is use on_change
        # after a button get clicked, the file will be run again
        uploaded_file = st.file_uploader(
            "Choose Hero Pools File", type=['json'], key=f"uploader_key", on_change=file_upload_onchange)


    if st.session_state['activate_basic_info_flag']:
        with st.form("player_basic_info"):
            pos_rad = st.radio("Player Position (if you can play multi-pos, or you want to submit your friends' hero pool, re-edit in the next round)", [
                'Pos 1 Carry',
                'Pos 2 Mid',
                'Pos 3 Offlane',
                'Pos 4 Ganker',
                'Pos 5 Support',
            ], index=4, key="form_pos_rad")

            playername = st.text_input("Player Name", "Gabe Newell", key="form_playername")
            st.form_submit_button("Next", on_click=player_basic_info_callback)

    if st.session_state['activate_hero_flag']: # add new content 
        st.toast("Go Ahead!", icon="🌟")
        with st.form("activate_hero_info"):
            for t in ["Strength", "Agility", "Intelligence", "Universal"]:
                with st.container():
                    st.markdown(f"""#### {t}""")
                    df = get_hero_csv_data(t)
                    # st.dataframe(df)
                    imgfilenames = list(df['Image filename'].str.strip())
                    heronames = list(df['Name'].str.strip())
                    img_array = get_image_data(imgfilenames)
                    toggle_vals = [False for _ in heronames]
                    for togi in range(len(toggle_vals)):
                        if heronames[togi] in st.session_state['target_hero_pool']:
                            toggle_vals[togi] = True
                    args_list = list(zip(img_array, heronames, toggle_vals))
                    row_display_component(args_list, image_width)
                    
            st.form_submit_button("Complete Your Edit", on_click=complete_edit_callback)
                
                
    if st.session_state['display_stats_flag']:
        # download 
        download_json = dict()
        download_json["ally_player_names"] = st.session_state["ally_player_names"]
        download_json["ally_hero_pools"] = st.session_state["ally_hero_pools"]
        download_json = json.dumps(download_json)
        download_button_placeholder.download_button("Download Your Hero Pool Json File",
                        download_json, "hero_pool_id_{st.session_state.data_ready_count}.json", key=f"dldbtn_{st.session_state.data_ready_count}")
        
        # display stats
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.subheader(st.session_state["ally_player_names"][i])
                st.write(st.session_state["ally_hero_pools"][i])
    # we shall have three options in the end
    # 1. continue edit
    # 2. download the file
    # 3. auto cache it

