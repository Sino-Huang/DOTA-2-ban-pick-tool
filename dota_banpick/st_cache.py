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
warmup_cache_dict_fp = os.path.join(
        record_folder, f"depth_limit_{DEPTH_LIMIT}_warmup_cache_dict.pkl")
hero_name_csv_fp = os.path.join(record_folder, "heronames.csv")
image_folder = os.path.join(os.path.dirname(__file__), "data/hero_wide_icons")
# ! wow, same cache_resource function will share over pages !

@st.cache_resource
def init_warmup_cache_dict():
    cache_dict_manager = Manager()
    if not os.path.exists(warmup_cache_dict_fp):
        st.warning("Warmup Cache Dict Missing")
    with open(warmup_cache_dict_fp, 'rb') as f:
        warmup_cache_dict = pickle.load(f)
    alpha_beta_cache_dict = cache_dict_manager.dict(warmup_cache_dict)
    return alpha_beta_cache_dict

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

@st.cache_resource
def load_cached_name_hero_pool_dict():
    singleton_manager = Manager()
    cache_dict = singleton_manager.dict()
    return cache_dict