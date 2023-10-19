import streamlit as st
import pandas as pd 
import os
import pickle 
from PIL import Image

record_folder = os.path.join(os.path.dirname(__file__), "../../data/records")
hero_name_csv_fp = os.path.join(record_folder, "heronames.csv")
image_folder = os.path.join(os.path.dirname(__file__), "../../data/hero_wide_icons")

image_width = 11 

st.set_page_config(
    layout="wide"
)

@st.cache_data
def get_hero_csv_data(t_type):
    df = pd.read_csv(hero_name_csv_fp, header=None)
    df.columns = ["Name", "Image filename", "Type"]
    df = df[df['Type'].str.strip() == t_type]
    return df

@st.cache_data
def get_image_data(imgfilenames):
    output_img_array = [] 
    for imgfn in imgfilenames:
        imgfp = os.path.join(image_folder, imgfn+".png")
        img = Image.open(imgfp)
        output_img_array.append(img)
        
    return output_img_array

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
    st.image(img)
    st.caption(name)

@st.cache_resource
def loading_page():
    for t in ["Strength", "Agility", "Intelligence", "Universal"]:
        with st.container():
            st.markdown(f"""## {t} Heroes""")
            df = get_hero_csv_data(t)
            # st.dataframe(df)
            imgfilenames = list(df['Image filename'].str.strip())
            heronames = list(df['Name'].str.strip())
            img_array = get_image_data(imgfilenames)
            args_list = list(zip(img_array, heronames))
            row_display_component(args_list, image_width)

loading_page()