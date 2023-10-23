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

from dota_banpick.st_cache import get_hero_csv_data_filtered, pos_description, get_hero_csv_data, get_heros, get_image_data, load_cached_name_hero_pool_dict, load_default_hero_pools



def row_display_component(component_arg_list, width):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_item_component(*args)
def delete_cache_player_data(k):
    cache_dict = load_cached_name_hero_pool_dict()
    cache_dict.pop(k)

def show_item_component(img, name, toggle_val = None):
    if toggle_val is not None:

        if " " in name:
            cap_text =  " ".join([x[:5] for x in name.split(" ")[:2]])
        else:
            cap_text = name
        st.image(img,  use_column_width="always")
        cols = st.columns(2)
        with cols[1]:
            st.caption(cap_text)
        with cols[0]:
            st.toggle("enable", label_visibility="collapsed", value=toggle_val, key=f"toggle_{name}")
            
    else:
        st.image(img,  use_column_width="always")

def player_basic_info_callback():
    pos_inds = []
    for multioutput in  st.session_state.form_pos_multi:
        pos_inds.append(pos_description.index(multioutput))
        
    pool_set = set()
    for pos_ind in pos_inds:
        for h in st.session_state["default_hero_pools"][pos_ind]:
            pool_set.add(h)
    # ! these are the keys for player data 
    st.session_state["target_hero_pool"] = list(pool_set)
    st.session_state["target_pos"] = pos_inds
    st.session_state["target_player_name"]= st.session_state.form_playername
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
    
    st.session_state['activate_hero_flag'] = False
    st.session_state['display_stats_flag'] = True
    st.session_state['activate_basic_info_flag'] = False
    
    # auto cache
    cache_dict = load_cached_name_hero_pool_dict()
    store_player_dict = dict()
    store_player_dict["target_hero_pool"] = st.session_state["target_hero_pool"] 
    store_player_dict["target_pos"]= st.session_state["target_pos"] 
    store_player_dict["target_player_name"] = st.session_state["target_player_name"]
    
    cache_dict[st.session_state["target_player_name"]] = store_player_dict
    
    # display stats 
    st.session_state.data_ready_count += 1
    
def input_user_info_callback():
    st.toast("Start Editing Your Own Hero Pool", icon="🌟")
    st.session_state['activate_hero_flag'] = False
    st.session_state['display_stats_flag'] = False
    st.session_state['activate_basic_info_flag'] = True
    
    
def file_upload_onchange():
    uploaded_file = st.session_state['uploader_key']
    
    if uploaded_file is not None:
        st.toast("Upload Local Hero Pools", icon="📂")
        heropool_json = uploaded_file.read()
        heropool_json = json.loads(heropool_json)
        uploaded_file = None
        if len(heropool_json) == 0:
            st.warning(
                "Not A Valid Hero Pools File, You Shall Try Other Methods!", icon="❤️‍🔥")
        else:
            cached_dict = load_cached_name_hero_pool_dict()
            cached_dict.clear()
            for k in heropool_json:
                cached_dict[k] = heropool_json[k]
            # display hero pool
            st.session_state['display_stats_flag'] = True
            st.session_state.data_ready_count += 1
    



image_width = 6

if __name__ == "__main__":
    st.set_page_config(
        layout="centered"
    )

    # default
    
    st.session_state.data_ready_count = 0

    if 'activate_basic_info_flag' not in st.session_state:
        st.session_state['activate_basic_info_flag'] = True
        
    if 'activate_hero_flag' not in st.session_state:
        st.session_state['activate_hero_flag'] = False
        
    if "display_stats_flag" not in st.session_state:
        st.session_state['display_stats_flag'] = False

    st.markdown("""
    <style>
    .small-font {
        font-size:11px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
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


    if "ally_player_names" not in st.session_state:
        st.session_state["ally_player_names"] = ['Pos 1 Bot',
                                                'Pos 2 Bot',
                                                'Pos 3 Bot',
                                                'Pos 4 Bot',
                                                'Pos 5 Bot'
                                                ]


    if "default_hero_pools" not in st.session_state:
        st.session_state["default_hero_pools"] = load_default_hero_pools()
        
    if 'allheroes' not in st.session_state:
        st.session_state["allheroes"] = get_heros()
    st.title("Edit Hero Pools")
    st.write("""You are required to provide your hero pool to run the BanPick tool,""")

    
    with st.sidebar:
        cache_dict = load_cached_name_hero_pool_dict()
        st.write("Currently in Cache:")
        dftable = pd.DataFrame(list(cache_dict.keys()), columns=['Player Name'])
        st.table(dftable)
        if len(dftable) > 0:
            showbut = st.button("Display Cache")
            if showbut:
                st.session_state['activate_hero_flag'] = False
                st.session_state['display_stats_flag'] = True
                st.session_state['activate_basic_info_flag'] = False
                st.rerun()
    
    
    if st.session_state['activate_basic_info_flag']:
        # ! so far solution is use on_change
        # after a button get clicked, the file will be run again
        uploaded_file = st.file_uploader(
            "You can also upload your hero pools file", type=['json'], key=f"uploader_key", on_change=file_upload_onchange)
        
        with st.form("player_basic_info"):
            pos_multi = st.multiselect("Player Position (if you can play multi-pos, or you want to submit your friends' hero pool, re-edit in the next round)", 
                                        pos_description, key="form_pos_multi", default=pos_description[-1])

            playername = st.text_input("Player Name", value="Player", placeholder="Gabe Newell", key="form_playername")
            st.form_submit_button("Next", on_click=player_basic_info_callback)

    if st.session_state['activate_hero_flag']: # add new content 
        st.info(f"Hi {st.session_state['target_player_name']}, please adjust your hero pool.")
        st.toast("Toggle hero items now!", icon="🌟")
        with st.form("activate_hero_info"):
            for t in ["Strength", "Agility", "Intelligence", "Universal"]:
                with st.expander(f"{t}", expanded=True):
                    df = get_hero_csv_data(t)
                    # st.dataframe(df)
                    df['If Reco'] = df['Name'].str.strip().isin(st.session_state['target_hero_pool'])
                    df = df.sort_values(by= ['If Reco'], ascending=False)
                    
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
        cache_dict = load_cached_name_hero_pool_dict()
        download_json = dict(cache_dict)
        download_json = json.dumps(download_json)
        cols = st.columns(2)
        with cols[0]:
            st.download_button("Download Your Hero Pool Json File",
                        download_json, f"hero_pool_id_{st.session_state.data_ready_count}.json", key=f"dldbtn_{st.session_state.data_ready_count}",
                        use_container_width=True, type="primary")
        with cols[1]:
            edit_again_but = st.button("Add/Edit Hero Pool Again", use_container_width=True, type="primary")
            if edit_again_but:
                st.session_state['activate_hero_flag'] = False
                st.session_state['display_stats_flag'] = False
                st.session_state['activate_basic_info_flag'] = True
                st.rerun()
        
        # display stats
        for k in cache_dict:
            with st.expander(k+"'s hero pool", expanded=True):
                heronames = cache_dict[k]['target_hero_pool']
                player_pos = cache_dict[k]['target_pos']
                df = get_hero_csv_data_filtered(heronames)
                imgfilenames = list(df['Image filename'].str.strip())
                img_array = get_image_data(imgfilenames)
                args_list = list(zip(img_array, heronames))
                row_display_component(args_list, 11) 
                delete_but = st.button("Delete Data", key=f"delete_but_{k}", on_click=delete_cache_player_data, args=(k,))
                
    # we shall have three options in the end
    # 1. continue edit
    # 2. download the file
    # 3. auto cache it

