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
from dota_banpick.config import DEPTH_LIMIT
from PIL import Image


record_folder = os.path.join(os.path.dirname(__file__), "data/records")

hero_name_csv_fp = os.path.join(record_folder, "heronames.csv")
image_folder = os.path.join(os.path.dirname(__file__), "data/hero_wide_icons")
# ! wow, same cache_resource function will share over pages !
pos_description = ['Pos 1 Carry',
                   'Pos 2 Mid',
                   'Pos 3 Offlane',
                   'Pos 4 Ganker',
                   'Pos 5 Support',
                   ]

@st.cache_resource
def get_position_colour_tags():
    output = [
        "#A5BE8F",
        "#3D87BB",
        "#DAB77F",
        "#DE5730",
        "#EC9DC3"
    ]
    return output 


@st.cache_resource
def get_position_default_imgspath():
    return [
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/juggernaut.png",
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/storm_spirit.png",
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/centaur.png",
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/rubick.png",
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/crystal_maiden.png"
    ]


@st.cache_data
def get_hero_csv_data(t_type):
    df = pd.read_csv(hero_name_csv_fp, header=None)
    df.columns = ["Name", "Image filename", "Type"]
    df = df[df['Type'].str.strip() == t_type]
    return df

@st.cache_data
def get_name_abbrev_dict():
    hero_abbrev_fp = os.path.join(record_folder, "hero_abbrev.csv")
    
    df = pd.read_csv(hero_abbrev_fp)
    output_dict = dict()
    for index, attr in df.iterrows():
        name = attr['Name']
        abbrev = attr['Abbrev']
        output_dict[name] = f"{abbrev} {name}"
    
    return output_dict
    
@st.cache_data
def get_pos_1_hero_list():
    with open(os.path.join(record_folder, 'default_pos_1_hero_pool.txt'), 'r') as f:
        s = f.read()
    return eval(s)


@st.cache_data
def get_pos_2_hero_list():
    with open(os.path.join(record_folder, 'default_pos_2_hero_pool.txt'), 'r') as f:
        s = f.read()
    return eval(s)


@st.cache_data
def get_pos_3_hero_list():
    with open(os.path.join(record_folder, 'default_pos_3_hero_pool.txt'), 'r') as f:
        s = f.read()
    return eval(s)


@st.cache_data
def get_pos_4_hero_list():
    with open(os.path.join(record_folder, 'default_pos_4_hero_pool.txt'), 'r') as f:
        s = f.read()
    return eval(s)


@st.cache_data
def get_pos_5_hero_list():
    with open(os.path.join(record_folder, 'default_pos_5_hero_pool.txt'), 'r') as f:
        s = f.read()
    return eval(s)


@st.cache_data
def get_hero_csv_data_filtered(hero_list):
    df = pd.read_csv(hero_name_csv_fp, header=None)
    df.columns = ["Name", "Image filename", "Type"]
    df = df[df['Name'].str.strip().isin(hero_list)]
    return df


@st.cache_data
def get_hero_csv_data_raw():
    df = pd.read_csv(hero_name_csv_fp, header=None)
    df.columns = ["Name", "Image filename", "Type"]
    df.index = list(df['Name'].str.strip())
    return df

@st.cache_data
def get_image_data(imgfilenames):
    output_img_array = []
    for imgfn in imgfilenames:
        imgfp = os.path.join(image_folder, imgfn+".png")

        img = Image.open(imgfp)
        output_img_array.append(img)

    return output_img_array


@st.cache_data
def get_heros():
    df = pd.read_csv(hero_name_csv_fp, header=None)
    df.columns = ["Name", "Image filename", "Type"]
    allheroes = list(df['Name'].str.strip())
    return allheroes


@st.cache_data
def load_default_hero_pools():
    hero_pool_fps = glob(os.path.join(
        record_folder, "default_pos_*_hero_pool.txt"))
    hero_pool_fps = natsorted(hero_pool_fps)
    default_hero_pools = []
    for hp_fp in hero_pool_fps:
        with open(hp_fp, 'r') as f:
            hp_text = f.read()
            default_hero_pools.append(eval(hp_text))
    return default_hero_pools  # structure [[hero_name]]


def load_cached_name_hero_pool_dict(): # no more cache because we want different users to use
    # singleton_manager = Manager()
    # cache_dict = singleton_manager.dict()
    # return cache_dict
    if "singleton_cache_dict" not in st.session_state:
        st.session_state.singleton_cache_dict = dict()
    return st.session_state.singleton_cache_dict
