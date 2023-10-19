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



record_folder = os.path.join(os.path.dirname(__file__), "data/records")
warmup_cache_dict_fp = os.path.join(
        record_folder, f"depth_limit_{DEPTH_LIMIT}_warmup_cache_dict.pkl")
st.set_page_config(
    page_title="DOTA 2 BP Tool",
    page_icon="✨"
)

@st.cache_resource
def init_warmup_cache_dict():
    cache_dict_manager = Manager()
    if not os.path.exists(warmup_cache_dict_fp):
        st.warning("Warmup Cache Dict Missing")
    with open(warmup_cache_dict_fp, 'rb') as f:
        warmup_cache_dict = pickle.load(f)
    alpha_beta_cache_dict = cache_dict_manager.dict(warmup_cache_dict)
    return alpha_beta_cache_dict

_ = init_warmup_cache_dict()



st.title("Welcome to DOTA2 BP Tool")
st.warning("Streamlit Version app can only be held locally, check https://discuss.streamlit.io/t/10-most-common-explanations-on-the-streamlit-forum/39054 for more details")

st.markdown("""## How to use this tool

1. first of all, this app needs to confirm your position and hero pool 
   - after you provide your position, it will present you default hero pool for that position, and you need to remove unfamiliar heroes.
   - after that, it will present you all other uncommon heroes for that position, you can still add some if you want
   - this hero pool can be downloaded or uploaded
2. then you can move to BanPick page 
   - each hero will be attached with a radio button with three choices - Ally, Oppo, Ban
   - the tool shall provide you drafting suggestion and also not-good heroes. """)