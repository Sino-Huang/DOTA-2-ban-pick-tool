# %% [markdown]
# # Stratz API calling gathering info
# - we slowly migrate from web scraping to API calling to get inforamtion

# %%
import os
import time
from lxml import html
import requests
import pickle
import json
from tqdm.auto import tqdm
from datetime import datetime
import subprocess
from dota_banpick import utils
import shutil
import pandas as pd

# %%
url = "https://api.stratz.com/graphql"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTliOTNjYmMtOWE3Mi00NzdhLWExYjEtNzZhMDgwM2VkMjBlIiwiU3RlYW1JZCI6IjgxNTU0Mzc2IiwibmJmIjoxNzEyODM2ODU2LCJleHAiOjE3NDQzNzI4NTYsImlhdCI6MTcxMjgzNjg1NiwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.DjsHo8I4XE9vAwYdXmWlVXUxvCEBfdzLhw7lLSp8jio"

hero_abbrev_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "../records/hero_abbrev.csv"))
HERO_LEN_M_ONE = len(hero_abbrev_df) - 1

# %%
# test
body = """
{
  heroStats {
    heroVsHeroMatchup(heroId: 2 bracketBasicIds: [CRUSADER_ARCHON, LEGEND_ANCIENT, DIVINE_IMMORTAL]) {
      advantage {
        heroId
        with {
          heroId2
          winsAverage
          synergy
          matchCount
        }
        vs {
          heroId2
          winsAverage
          synergy
          matchCount
        }
      }
    }
  }
}
"""
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}
response = requests.post(url=url, json={"query": body}, headers=headers)
print("response status code: ", response.status_code)
output_dict = json.loads(response.content.decode())

# %% [markdown]
# ## obtain id to name
#

# %%
# id_to name query
body = """
{
  constants{
    heroes{
      id
      displayName
    }
  }
}
"""
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}
response = requests.post(url=url, json={"query": body}, headers=headers)
print("response status code: ", response.status_code)
id_to_name_dict_json = json.loads(response.content.decode())

# %%
id_to_name_dict = dict()
id_to_name_content = id_to_name_dict_json['data']['constants']['heroes']
for d in tqdm(id_to_name_content):
    id_to_name_dict[d['id']] = d['displayName']

# %%


def parse_graphql_output(output_dict, id_to_name_dict):
    counter_rate_list = []
    versus_winrate_list = []
    with_winrate_list = []
    synergy_rate_list = []
    try:
        content = output_dict['data']['heroStats']['heroVsHeroMatchup']['advantage'][0]
    except Exception as e:
      print(e)
      # breakpoint()
      raise e
      
    hero_id = content['heroId']
    hero_name = id_to_name_dict[hero_id]
    with_list = content['with']
    vs_list = content['vs']
    try:
        list_length_error_flag = False
        assert len(
            with_list) == HERO_LEN_M_ONE, f"with list length is {len(with_list)}\n {with_list}"
        assert len(vs_list) == HERO_LEN_M_ONE, f"vs list length is {len(vs_list)}"
    except Exception as e:
        list_length_error_flag = True
        print(e)
        print(f"The length is not {HERO_LEN_M_ONE} for with len {len(with_list)} or vs len {len(vs_list)}")
      
    with_win_rate_avg = 0
    synergy_avg = 0
    for d in with_list:
        tar_hero_id = d['heroId2']
        tar_hero_name = id_to_name_dict[tar_hero_id]
        with_win_rate = d['winsAverage']
        with_win_rate_avg += with_win_rate
        synergy_rate = d['synergy'] / 100.0
        synergy_avg += synergy_rate
        synergy_rate_list.append((tar_hero_name, synergy_rate))
        with_winrate_list.append((tar_hero_name, with_win_rate))
    with_win_rate_avg /= len(with_list)
    synergy_avg /= len(with_list)
        
    if list_length_error_flag:
        hero_names = list(id_to_name_dict.values())
        heros_not_in_with = set(hero_names) - set([d[0] for d in with_winrate_list])
        for hname in heros_not_in_with:
            with_winrate_list.append((hname, with_win_rate_avg))
            synergy_rate_list.append((hname, synergy_avg))
          
    versus_win_rate_avg = 0
    counter_rate_avg = 0
    for d in vs_list:
        tar_hero_id = d['heroId2']
        tar_hero_name = id_to_name_dict[tar_hero_id]
        versus_win_rate = d['winsAverage']
        counter_rate = d['synergy'] / 100.0
        versus_win_rate_avg += versus_win_rate
        counter_rate_avg += counter_rate
        counter_rate_list.append((tar_hero_name, counter_rate))
        versus_winrate_list.append((tar_hero_name, versus_win_rate))
    versus_win_rate_avg /= len(vs_list)
    counter_rate_avg /= len(vs_list)
    
    if list_length_error_flag:
        hero_names = list(id_to_name_dict.values())
        heros_not_in_vs = set(hero_names) - set([d[0] for d in versus_winrate_list])
        for hname in heros_not_in_vs:
            versus_winrate_list.append((hname, versus_win_rate_avg))
            counter_rate_list.append((hname, counter_rate_avg))
        
        

    # sort
    # counter most to counter least
    counter_rate_list = sorted(
        counter_rate_list, key=lambda x: x[1], reverse=True)
    versus_winrate_list = sorted(
        versus_winrate_list, key=lambda x: x[1], reverse=True)  # win most to win least
    with_winrate_list = sorted(
        with_winrate_list, key=lambda x: x[1], reverse=True)  # win most to win least
    # good with most to least
    synergy_rate_list = sorted(
        synergy_rate_list, key=lambda x: x[1], reverse=True)
    # get dict
    counter_rate_dict = {n: v for n, v in counter_rate_list}
    versus_winrate_dict = {n: v for n, v in versus_winrate_list}
    with_winrate_dict = {n: v for n, v in with_winrate_list}
    synergy_rate_dict = {n: v for n, v in synergy_rate_list}

    return hero_name, counter_rate_dict, versus_winrate_dict, synergy_rate_dict, with_winrate_dict


# %%
parse_graphql_output(output_dict, id_to_name_dict)[1]

# %% [markdown]
# ## Generate matrix

# %%
all_hero_ids = id_to_name_dict.keys()
counter_rate_matrix = dict()
versus_winrate_matrix = dict()
synergy_rate_matrix = dict()
with_winrate_matrix = dict()
print("GETTING WINRATE INFO...")
for id in (qbar := tqdm(all_hero_ids)):
    qbar.set_description(f"Processing {id}, name {id_to_name_dict[id]}")
    body = """
{{
  heroStats {{
    heroVsHeroMatchup(heroId: {cid} bracketBasicIds: [LEGEND_ANCIENT, CRUSADER_ARCHON, DIVINE_IMMORTAL]) {{
      advantage {{
        heroId
        with {{
          heroId2
          winsAverage
          synergy
          matchCount
        }}
        vs {{
          heroId2
          winsAverage
          synergy
          matchCount
        }}
      }}
    }}
  }}
}}
""".format(cid=id)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try_limit = 5
    try_count = 0
    while try_count < try_limit:
        try:
            response = requests.post(url=url, json={"query": body}, headers=headers)
            # print("response status code: ", response.status_code)
            if response.status_code != 200:
                print("GG, not equal 200")
                break
            output_dict = json.loads(response.content.decode())
            hero_name, counter_rate_dict, versus_winrate_dict, synergy_rate_dict, with_winrate_dict = parse_graphql_output(
                output_dict, id_to_name_dict)
            counter_rate_matrix[hero_name] = counter_rate_dict
            versus_winrate_matrix[hero_name] = versus_winrate_dict
            synergy_rate_matrix[hero_name] = synergy_rate_dict
            with_winrate_matrix[hero_name] = with_winrate_dict
            break
        except Exception as e:
            print("Error for ", id, id_to_name_dict[id])
            print("Retry after 1 second")
            try_count += 1
            time.sleep(1)
        

# %%
# save them
with open(os.path.join(os.path.dirname(__file__), "../records/counter_rate_matrix.pkl"), 'wb') as f:
    pickle.dump(counter_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../records/versus_winrate_matrix.pkl"), 'wb') as f:
    pickle.dump(versus_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../records/synergy_rate_matrix.pkl"), 'wb') as f:
    pickle.dump(synergy_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../records/with_winrate_matrix.pkl"), 'wb') as f:
    pickle.dump(with_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)


# %%
# save them to deployment env
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/counter_rate_matrix.pkl"), 'wb') as f:
    pickle.dump(counter_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/versus_winrate_matrix.pkl"), 'wb') as f:
    pickle.dump(versus_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/synergy_rate_matrix.pkl"), 'wb') as f:
    pickle.dump(synergy_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/with_winrate_matrix.pkl"), 'wb') as f:
    pickle.dump(with_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

# %%
date_str = datetime.now().strftime("%d %B %Y")
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/update_time.txt"), 'w') as f:
    f.write(date_str)

# %% [markdown]
# ## Lane INFO

# %%

# %%
ids = [h['id'] for h in id_to_name_dict_json['data']['constants']['heroes']]
hero_names = [h['displayName']
              for h in id_to_name_dict_json['data']['constants']['heroes']]

# %%
print("GETTING LANE INFO...")
lane_names = ['Safe lane', 'Mid Lane',
              'Off Lane', 'Soft Support', 'Hard Support']
pick_rate_name = ['Pos 1 Pick Rate', 'Pos 2 Pick Rate',
                  'Pos 3 Pick Rate', 'Pos 4 Pick Rate', 'Pos 5 Pick Rate']
lane_rate_info_dict = dict()
for heroind, id in enumerate(tqdm(ids)):
    hname = hero_names[heroind]
    lane_rate_info_dict[hname] = dict()
    url = f"https://stratz.com/heroes/{id}"
    lane_rate_info_dict[hname]['url'] = url

    body = """
{{
  heroStats{{
    stats(heroIds:[{cid}] bracketBasicIds:[LEGEND_ANCIENT, DIVINE_IMMORTAL, CRUSADER_ARCHON] positionIds:[POSITION_1, POSITION_2, POSITION_3, POSITION_4, POSITION_5] groupByPosition:true){{
      
      matchCount
    }}
  }}
}}
""".format(cid=id)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try_limit = 5
    try_count = 0
    while try_count < try_limit:
        try:
            response = requests.post(
                url="https://api.stratz.com/graphql", json={"query": body}, headers=headers)
            # print("response status code: ", response.status_code)
            if response.status_code != 200:
                print(f"GG, LANE INFO not equal 200 for {id} {hname}")
                break
            output_dict = json.loads(response.content.decode())
            lane_counts = [h['matchCount']
                          for h in output_dict['data']['heroStats']['stats']]
            
            break
        except Exception as e:
            print(e)
            print(f"Error for {id} {hname}")
            print("Retry after 1 second")
            try_count += 1
            time.sleep(1)
            # breakpoint()
    lane_pick_rates = [h/sum(lane_counts) for h in lane_counts]

    for lane_ind, lanen in enumerate(lane_names):
        lane_rate_info_dict[hname][pick_rate_name[lane_ind]
                                   ] = lane_pick_rates[lane_ind]


# %%
# save them
with open(os.path.join(os.path.dirname(__file__),"../records/lane_rate_info_dict.pkl"), 'wb') as f:
    pickle.dump(lane_rate_info_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/lane_rate_info_dict.pkl"), 'wb') as f:
    pickle.dump(lane_rate_info_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# %% [markdown]
# ## Everyday Winrate

# %%
print("GETTING EVERYDAY WINRATE INFO...")
hero_winrate_dict = dict()
ids = [h['id'] for h in id_to_name_dict_json['data']['constants']['heroes']]
hero_names = [h['displayName']
              for h in id_to_name_dict_json['data']['constants']['heroes']]
for heroind, id in enumerate(tqdm(ids)):
    hname = hero_names[heroind]
    hero_winrate_dict[hname] = dict()
    url = f"https://stratz.com/heroes/{id}"
    hero_winrate_dict[hname]['url'] = url
    body = """
{{
  heroStats {{
    winHour(heroIds: {cid} bracketIds: [IMMORTAL, DIVINE, ANCIENT, LEGEND, ARCHON]){{
      hour
      winCount
      matchCount
    }}
  }}
}}
""".format(cid=id)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try_limit = 5
    try_count = 0
    while try_count < try_limit:
        try:

            response = requests.post(
                url="https://api.stratz.com/graphql", json={"query": body}, headers=headers)
            # print("response status code: ", response.status_code)
            if response.status_code != 200:
                print(f"GG, EVERYDAY WINRATE not equal 200 for {id} {hname}")
                break
            output_dict = json.loads(response.content.decode())
            win_counts = sum([h['winCount']
                            for h in output_dict['data']['heroStats']['winHour']])
            match_counts = sum([h['matchCount']
                              for h in output_dict['data']['heroStats']['winHour']])
            hero_winrate_dict[hname]['winrate'] = win_counts / match_counts
            break
        except Exception as e:
            print(e)
            print(f"Error for {id} {hname}")
            print("Retry after 1 second")
            try_count += 1
            time.sleep(1)
            # breakpoint()

# sort the winrate dict
hero_winrate_dict = dict(sorted(hero_winrate_dict.items(
), key=lambda item: item[1]['winrate'], reverse=True))

# %%
# save them
with open(os.path.join(os.path.dirname(__file__),"../records/hero_winrate_info_dict.pkl"), 'wb') as f:
    pickle.dump(hero_winrate_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/hero_winrate_info_dict.pkl"), 'wb') as f:
    pickle.dump(hero_winrate_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# %% [markdown]
# ## Lane win is win
# - get lane win info

# %%
print("ANALYZING DETAILED LANE WIN INFO...")
hero_lanewin_versus_dict = dict()
hero_lanewin_with_dict = dict()
ids = [h['id'] for h in id_to_name_dict_json['data']['constants']['heroes']]
hero_names = [h['displayName']
              for h in id_to_name_dict_json['data']['constants']['heroes']]
for heroind, id in enumerate(tqdm(ids)):
    hname = hero_names[heroind]
    hero_lanewin_versus_dict[hname] = dict()
    hero_lanewin_with_dict[hname] = dict()

    body_versus = """
{{
	heroStats{{
    laneOutcome(isWith: {is_with} heroId: {cid} bracketBasicIds:[DIVINE_IMMORTAL, LEGEND_ANCIENT, CRUSADER_ARCHON]){{
      heroId1
      heroId2
      matchCount
      winCount
      stompWinCount
      matchCount
      matchWinCount
    }}
  }}
}}
""".format(cid=id, is_with="false")
    body_with = """
{{
	heroStats{{
    laneOutcome(isWith: {is_with} heroId: {cid} bracketBasicIds:[DIVINE_IMMORTAL, LEGEND_ANCIENT, CRUSADER_ARCHON]){{
      heroId1
      heroId2
      matchCount
      winCount
      stompWinCount
      matchCount
      matchWinCount
    }}
  }}
}}
""".format(cid=id, is_with="true")
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try_limit = 5
    try_count = 0
    while try_count < try_limit:
        try:
            response_versus = requests.post(
                url="https://api.stratz.com/graphql", json={"query": body_versus}, headers=headers)
            response_with = requests.post(
                url="https://api.stratz.com/graphql", json={"query": body_with}, headers=headers)

            # print("response status code: ", response.status_code)
            if response_versus.status_code != 200:
                print(f"GG, LANE WIN IS WIN not equal 200 for {id} {hname}")
                break
            output_dict_versus = json.loads(response_versus.content.decode())[
                'data']['heroStats']['laneOutcome']
            output_dict_with = json.loads(response_with.content.decode())[
                'data']['heroStats']['laneOutcome']
            break
        except Exception as e:
            print(e)
            print(f"Error for {id} {hname}")
            print("Retry after 1 second")
            try_count += 1
            time.sleep(1)
            # breakpoint()
    for sd in output_dict_versus:
        assert sd['heroId1'] == id
        matchCount = sd['matchCount']
        if matchCount <= 100:
            continue
        winCount = sd['winCount']
        stompWinCount = sd['stompWinCount']
        winlane_rate = (winCount + stompWinCount) / matchCount
        matchWinCount = sd['matchWinCount']
        win_rate = matchWinCount / matchCount
        score = win_rate*0.4 + winlane_rate * 0.6
        target_hero_id = sd['heroId2']
        target_hero_ind = ids.index(target_hero_id)
        target_hname = hero_names[target_hero_ind]
        hero_lanewin_versus_dict[hname][target_hname] = score
    for sd in output_dict_with:
        assert sd['heroId1'] == id
        matchCount = sd['matchCount']
        if matchCount <= 100:
            continue
        winCount = sd['winCount']
        stompWinCount = sd['stompWinCount']
        winlane_rate = (winCount + stompWinCount) / matchCount
        matchWinCount = sd['matchWinCount']
        win_rate = matchWinCount / matchCount
        score = win_rate*0.4 + winlane_rate * 0.6
        target_hero_id = sd['heroId2']
        target_hero_ind = ids.index(target_hero_id)
        target_hname = hero_names[target_hero_ind]
        hero_lanewin_with_dict[hname][target_hname] = score

# sort
for k in hero_lanewin_with_dict:
    hero_lanewin_with_dict[k] = dict(sorted(
        hero_lanewin_with_dict[k].items(), key=lambda item: item[1], reverse=True))
for k in hero_lanewin_versus_dict:
    hero_lanewin_versus_dict[k] = dict(
        sorted(hero_lanewin_versus_dict[k].items(), key=lambda item: item[1]))

# sort the winrate dict
# hero_winrate_dict = dict(sorted(hero_winrate_dict.items(), key=lambda item: item[1]['winrate'], reverse=True))

# %%
# save them
with open(os.path.join(os.path.dirname(__file__),"../records/hero_lanewin_versus_dict.pkl"), 'wb') as f:
    pickle.dump(hero_lanewin_versus_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/hero_lanewin_versus_dict.pkl"), 'wb') as f:
    pickle.dump(hero_lanewin_versus_dict, f, protocol=pickle.HIGHEST_PROTOCOL)


# save them
with open(os.path.join(os.path.dirname(__file__),"../records/hero_lanewin_with_dict.pkl"), 'wb') as f:
    pickle.dump(hero_lanewin_with_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env
with open(os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/hero_lanewin_with_dict.pkl"), 'wb') as f:
    pickle.dump(hero_lanewin_with_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# %% [markdown]
# ## Warmup Cache Dict

# %%
utils.generate_warmup_cache(depth_limit=1)

# %%
# save to preprocess
src_warmup_dict_fp = os.path.join(os.path.dirname(__file__), "../../dota_banpick/data/records/depth_limit_1_warmup_cache_dict.pkl")
dst_warmup_dict_fp = os.path.join(os.path.dirname(__file__), "../records/depth_limit_1_warmup_cache_dict.pkl")
shutil.copyfile(src_warmup_dict_fp, dst_warmup_dict_fp)

# %%
# run the server
script_path = os.path.expanduser("~/opt/autostart/run_banpick_website.sh")
subprocess.run(['bash', script_path])

# %%
