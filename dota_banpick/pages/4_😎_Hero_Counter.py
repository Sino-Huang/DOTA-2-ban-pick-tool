import streamlit as st
import pandas as pd
import os
import pickle
from PIL import Image

from dota_banpick.st_cache import get_hero_csv_data, get_hero_csv_data_raw, get_image_data, get_name_abbrev_dict, get_position_colour_tags, pos_description
from dota_banpick.heuristic import compute_with_and_counter_heroes_for_each_pos
from streamlit_extras.image_in_tables import table_with_images
from annotated_text import annotated_text
from dota_banpick.config import default_hero_pools
from streamlit.errors import StreamlitAPIException

suggest_num = 6


def hero_pick_selectbox_to_counter_on_change():
    heroname = st.session_state['hero_pick_selectbox_to_counter']
    if heroname is None:
        return
    with_dict, counter_dict = compute_with_and_counter_heroes_for_each_pos(
        heroname, suggest_num)
    st.session_state['p4_target_hero_with_dict'] = with_dict
    st.session_state['p4_target_hero_counter_dict'] = counter_dict
    st.session_state['p4_target_hero'] = heroname


def get_online_image_urls(heronames):
    imgfilenames = list(
        st.session_state['raw_df']['Image filename'].loc[list(heronames)].str.strip())
    lst = [
        f'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{x}.png' for x in imgfilenames]
    return lst


def row_display_component(component_arg_list, width, show_compo_func):
    chunks_width = []
    for i in range(0, len(component_arg_list), width):
        chunks_width.append(component_arg_list[i: i+width])
    for chunk in chunks_width:
        cols = st.columns(width)
        for i, args in enumerate(chunk):
            with cols[i]:
                show_compo_func(*args)

def display_table(title, pos_ind, table):
    annotated_text("Recommended heroes if you play ", (pos_description[pos_ind].split(
                        " ")[-1], f"pos {pos_ind + 1}", get_position_colour_tags()[pos_ind]))
    st.markdown(table_with_images(df=table,
                                  url_columns=['Bad Against', 'Good With']),
                unsafe_allow_html=True)
    
    st.divider()

if __name__ == "__main__":
    try:
        st.set_page_config(
            layout="centered"
        )
    except StreamlitAPIException:
        pass

    if 'name_abbrev_dict' not in st.session_state:
        st.session_state['name_abbrev_dict'] = get_name_abbrev_dict()
        st.session_state['name_abbrev_dict_keys_list'] = list(
            st.session_state['name_abbrev_dict'].keys())

    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = get_hero_csv_data_raw()

    st.title("Know How to Matchup With a Hero")
    st.selectbox(f"Hero",
                 options=st.session_state['name_abbrev_dict_keys_list'],
                 format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                 index=None,
                 key=f"hero_pick_selectbox_to_counter",
                 on_change=hero_pick_selectbox_to_counter_on_change,)

    if 'p4_target_hero_with_dict' in st.session_state:
        st.subheader(f"{st.session_state['p4_target_hero']}")
        tcol = st.columns([0.65, 0.35])
        with tcol[0]:
            st.image(get_online_image_urls(
                [st.session_state['p4_target_hero']])[0])
        with tcol[1]:
            st.caption("Common Pos")
            for pos_ind, pool in enumerate(default_hero_pools):
                if st.session_state['p4_target_hero'] in pool:
                    annotated_text((pos_description[pos_ind].split(
                        " ")[-1], f"pos {pos_ind + 1}", get_position_colour_tags()[pos_ind]))
        st.subheader("Match Up Stats")
        heroname = st.session_state['p4_target_hero']
        # st.info(f"请根据你的位置, 查看推荐英雄, 如果{heroname}是你的队友在玩, 你可以选择Good With一栏的英雄配合{heroname}, 如果{heroname}是敌人在玩, 你可以选择Bad Against一栏的英雄克制{heroname}")
        st.info(f"Please check for recommended heroes based on your position. If {heroname} is on the opposing team, you can choose heroes listed in the 'Bad Against' column to counter {heroname}. If {heroname} is on your team, you can choose heroes listed in the 'Good With' column to complement {heroname}.")
        
        output_args = []
        for col_ind in range(5):
            position = col_ind+1
            dataframe = {
                "Bad Against": get_online_image_urls(st.session_state['p4_target_hero_counter_dict'][position]),
                "Good With": get_online_image_urls(st.session_state['p4_target_hero_with_dict'][position])
            }
            dataframe = pd.DataFrame(dataframe)
            output_args.append((f"Position {position}", col_ind, dataframe))

        row_display_component(output_args, 3, display_table)
