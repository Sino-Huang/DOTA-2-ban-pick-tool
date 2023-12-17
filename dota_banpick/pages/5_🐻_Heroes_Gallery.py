import streamlit as st
import pandas as pd 
import os
import pickle 
from PIL import Image

from dota_banpick.st_cache import get_hero_csv_data, get_image_data
from streamlit_js_eval import streamlit_js_eval


image_width = 10 
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
    st.image(img, caption=name,  use_column_width="always")



if __name__ == "__main__":
    st.set_page_config(
        layout="centered"
    )
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

    @st.cache_resource
    def loading_page():
        for t in ["Strength", "Agility", "Intelligence", "Universal"]:
            with st.expander(f"""## {t} Heroes""", expanded=True):
                df = get_hero_csv_data(t)
                # st.dataframe(df)
                imgfilenames = list(df['Image filename'].str.strip())
                heronames = list(df['Name'].str.strip())
                img_array = get_image_data(imgfilenames)
                args_list = list(zip(img_array, heronames))
                row_display_component(args_list, image_width)

    loading_page()