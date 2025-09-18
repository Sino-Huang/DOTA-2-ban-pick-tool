import streamlit as st
import pandas as pd
import os
import pickle
from PIL import Image

from dota_banpick.st_cache import hero_counter_display_table, hero_counter_row_display_component, get_online_image_urls, get_hero_csv_data, get_hero_csv_data_raw, get_image_data, get_name_abbrev_dict, get_position_colour_tags, pos_description
from dota_banpick.heuristic import compute_with_and_counter_heroes_for_each_pos
from streamlit_extras.image_in_tables import table_with_images
from annotated_text import annotated_text
from dota_banpick.config import default_hero_pools
from streamlit.errors import StreamlitAPIException

suggest_num = 6


def hero_pick_selectbox_to_counter_on_change():
    heronames = st.session_state['hero_pick_selectbox_to_counter']
    if heronames is None or heronames == []:
        return
    with_dict, counter_dict, bad_counter_dict = compute_with_and_counter_heroes_for_each_pos(
        heronames, suggest_num)
    st.session_state['p4_target_hero_with_dict'] = with_dict
    st.session_state['p4_target_hero_counter_dict'] = counter_dict
    st.session_state['p4_target_hero_bad_counter_dict'] = bad_counter_dict

    st.session_state['p4_target_hero'] = heronames





if __name__ == "__main__":
    try:
        st.set_page_config(
            layout="wide"
        )
    except StreamlitAPIException:
        pass

    if 'name_abbrev_dict' not in st.session_state:
        st.session_state['name_abbrev_dict'] = get_name_abbrev_dict()
        st.session_state['name_abbrev_dict_keys_list'] = list(
            st.session_state['name_abbrev_dict'].keys())

    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = get_hero_csv_data_raw()

    st.title("Know How to Counter/Coop Heroes 后知后觉，英雄克制与合作建议 🤖")
    st.info("This can be seen as a simplified version of ban pick suggestions. ")
    main_cols = st.columns(2)
    with main_cols[0]:
        st.multiselect(f"What Pos You Play",
                       options=["1", "2", "3", "4", "5"],
                    key=f"player_pos_multiselect",
                    on_change=hero_pick_selectbox_to_counter_on_change,)
        
    with main_cols[1]:
        st.multiselect(f"输入你关注的英雄 (可以是敌方或我方的)",
                    options=st.session_state['name_abbrev_dict_keys_list'],
                    format_func=lambda x: st.session_state['name_abbrev_dict'][x],
                    key=f"hero_pick_selectbox_to_counter",
                    on_change=hero_pick_selectbox_to_counter_on_change,)

    if 'p4_target_hero_with_dict' in st.session_state:

        st.subheader("Match Up Stats")
        heroname = st.session_state['p4_target_hero']
        st.info(f"请根据你的位置, 查看推荐英雄, 如果{heroname}是你的队友在玩, 你可以选择Good With一栏的英雄配合{heroname}, 如果{heroname}是敌人在玩, 你可以选择CNTR Pick一栏的英雄克制{heroname}，避免选择Avoid Pick一栏的英雄, 这些英雄会被{heroname}克制。")
        

        output_args = []
        for col_ind in range(5):
            position = col_ind+1
            if st.session_state['player_pos_multiselect'] != []:
                if str(position) not in st.session_state['player_pos_multiselect']:
                    continue
            dataframe = {
                "CNTR Pick": get_online_image_urls(st.session_state['p4_target_hero_counter_dict'][position]),
                "Good With": get_online_image_urls(st.session_state['p4_target_hero_with_dict'][position]),
                "Avoid Pick": get_online_image_urls(st.session_state['p4_target_hero_bad_counter_dict'][position]),
            }
            dataframe = pd.DataFrame(dataframe)
            output_args.append((f"Position {position}", col_ind, dataframe))

        hero_counter_row_display_component(output_args, 3, hero_counter_display_table)
        # st.info((f"Please check for recommended heroes based on your position. "
        #          f"If the selected heroes are on the opposing team, you can choose heroes listed in the 'CNTR Pick' column to counter them."
        #          f"If the selected heroes are on your team, you can choose heroes listed in the 'Good With' column to complement them. "
        #          f"Avoid pick heroes listed in the 'Avoid Pick' column as they are countered by the selected heroes."))
        
        st.subheader(f"Target Heroes")
        pos_cols = st.columns(10)
        for pos_info_i, the_hero in enumerate(st.session_state['p4_target_hero']):
            with pos_cols[pos_info_i]:
                st.image(get_online_image_urls(
                    [st.session_state['p4_target_hero'][pos_info_i]]), width=100, caption=st.session_state['p4_target_hero'][pos_info_i])
                for pos_ind, pool in enumerate(default_hero_pools):
                        if the_hero in pool:
                            annotated_text((pos_description[pos_ind].split(
                                " ")[-1], f"pos {pos_ind + 1}", get_position_colour_tags()[pos_ind]))
