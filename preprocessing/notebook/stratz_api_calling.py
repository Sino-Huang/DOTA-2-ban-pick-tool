# %% [markdown]
# # Stratz API calling gathering info
# - we slowly migrate from web scraping to API calling to get inforamtion

# %%
import requests 
import pickle 
import json
from tqdm.auto import tqdm
from datetime import datetime
import subprocess

# %%
url = "https://api.stratz.com/graphql"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTliOTNjYmMtOWE3Mi00NzdhLWExYjEtNzZhMDgwM2VkMjBlIiwiU3RlYW1JZCI6IjgxNTU0Mzc2IiwibmJmIjoxNjk5NTE2NTE0LCJleHAiOjE3MzEwNTI1MTQsImlhdCI6MTY5OTUxNjUxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.kxDkkVFpVvUAAP6rMePzWHGgQCl47YdJb2XuAFKO5XU"

# %%
# test
body="""
{
  heroStats {
    heroVsHeroMatchup(heroId: 2 bracketBasicIds: [LEGEND_ANCIENT, DIVINE_IMMORTAL]) {
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
headers= {
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
body="""
{
  constants{
    heroes{
      id
      displayName
    }
  }
}
"""
headers= {
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
    content = output_dict['data']['heroStats']['heroVsHeroMatchup']['advantage'][0]
    hero_id = content['heroId']
    hero_name = id_to_name_dict[hero_id]
    with_list = content['with']
    vs_list = content['vs']
    assert len(with_list) == 123
    assert len(vs_list) == 123
    for d in with_list:
        tar_hero_id = d['heroId2']
        tar_hero_name = id_to_name_dict[tar_hero_id]
        with_win_rate = d['winsAverage']
        synergy_rate = d['synergy'] / 100.0
        synergy_rate_list.append((tar_hero_name, synergy_rate))
        with_winrate_list.append((tar_hero_name, with_win_rate))

    for d in vs_list:
        tar_hero_id = d['heroId2']
        tar_hero_name = id_to_name_dict[tar_hero_id]
        versus_win_rate = d['winsAverage']
        counter_rate = d['synergy']/ 100.0
        counter_rate_list.append((tar_hero_name, counter_rate))
        versus_winrate_list.append((tar_hero_name, versus_win_rate))


    # sort 
    counter_rate_list = sorted(counter_rate_list, key=lambda x: x[1], reverse=True) # counter most to counter least
    versus_winrate_list = sorted(versus_winrate_list, key=lambda x: x[1], reverse=True) # win most to win least
    with_winrate_list = sorted(with_winrate_list, key=lambda x: x[1], reverse=True) # win most to win least
    synergy_rate_list  = sorted(synergy_rate_list, key=lambda x: x[1], reverse=True) # good with most to least
    # get dict 
    counter_rate_dict = {n:v for n, v in counter_rate_list}
    versus_winrate_dict = {n:v for n, v in versus_winrate_list}
    with_winrate_dict = {n:v for n, v in with_winrate_list}
    synergy_rate_dict = {n:v for n, v in synergy_rate_list}

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

for id in tqdm(all_hero_ids):
    body="""
{{
  heroStats {{
    heroVsHeroMatchup(heroId: {cid} bracketBasicIds: [LEGEND_ANCIENT, DIVINE_IMMORTAL]) {{
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
    headers= {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
          }
    response = requests.post(url=url, json={"query": body}, headers=headers)
    # print("response status code: ", response.status_code)
    if response.status_code != 200:
        print("GG, not equal 200")
        break
    output_dict = json.loads(response.content.decode())
    hero_name, counter_rate_dict, versus_winrate_dict, synergy_rate_dict, with_winrate_dict = parse_graphql_output(output_dict, id_to_name_dict)
    counter_rate_matrix[hero_name] = counter_rate_dict
    versus_winrate_matrix[hero_name] = versus_winrate_dict
    synergy_rate_matrix[hero_name] = synergy_rate_dict
    with_winrate_matrix[hero_name] = with_winrate_dict

# %%
# save them 
with open("../records/counter_rate_matrix.pkl", 'wb') as f:
    pickle.dump(counter_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../records/versus_winrate_matrix.pkl", 'wb') as f:
    pickle.dump(versus_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../records/synergy_rate_matrix.pkl", 'wb') as f:
    pickle.dump(synergy_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../records/with_winrate_matrix.pkl", 'wb') as f:
    pickle.dump(with_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)


# %%
# save them to deployment env 
with open("../../dota_banpick/data/records/counter_rate_matrix.pkl", 'wb') as f:
    pickle.dump(counter_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../../dota_banpick/data/records/versus_winrate_matrix.pkl", 'wb') as f:
    pickle.dump(versus_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../../dota_banpick/data/records/synergy_rate_matrix.pkl", 'wb') as f:
    pickle.dump(synergy_rate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

with open("../../dota_banpick/data/records/with_winrate_matrix.pkl", 'wb') as f:
    pickle.dump(with_winrate_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

# %%
date_str = datetime.now().strftime("%d %B %Y")
with open("../../dota_banpick/update_time.txt", 'w') as f:
    f.write(date_str)

# %% [markdown]
# ## Lane INFO

# %%
from lxml import html

# %%
ids = [h['id'] for h in id_to_name_dict_json['data']['constants']['heroes']]
hero_names = [h['displayName'] for h in id_to_name_dict_json['data']['constants']['heroes']]

# %%
lane_names = ['Safe lane', 'Mid Lane', 'Off Lane', 'Soft Support', 'Hard Support']
pick_rate_name = ['Pos 1 Pick Rate', 'Pos 2 Pick Rate', 'Pos 3 Pick Rate', 'Pos 4 Pick Rate', 'Pos 5 Pick Rate']
lane_rate_info_dict = dict()
for heroind, id in enumerate(tqdm(ids)):
    hname = hero_names[heroind]
    lane_rate_info_dict[hname] = dict()
    url = f"https://stratz.com/heroes/{id}"
    lane_rate_info_dict[hname]['url'] = url

    body="""
{{
  heroStats{{
    stats(heroIds:[{cid}] bracketBasicIds:[LEGEND_ANCIENT, DIVINE_IMMORTAL] positionIds:[POSITION_1, POSITION_2, POSITION_3, POSITION_4, POSITION_5] groupByPosition:true){{
      
      matchCount
    }}
  }}
}}
""".format(cid=id)
    headers= {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
          }
    response = requests.post(url="https://api.stratz.com/graphql", json={"query": body}, headers=headers)
    # print("response status code: ", response.status_code)
    if response.status_code != 200:
        print(f"GG, LANE INFO not equal 200 for {id} {hname}")
        break
    output_dict = json.loads(response.content.decode())
    lane_counts = [h['matchCount'] for h in output_dict['data']['heroStats']['stats']]
    lane_pick_rates = [h/sum(lane_counts) for h in lane_counts]

    for lane_ind, lanen in enumerate(lane_names):
        lane_rate_info_dict[hname][pick_rate_name[lane_ind]] = lane_pick_rates[lane_ind]
            
            

# %%
# save them 
with open("../records/lane_rate_info_dict.pkl", 'wb') as f:
    pickle.dump(lane_rate_info_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env 
with open("../../dota_banpick/data/records/lane_rate_info_dict.pkl", 'wb') as f:
    pickle.dump(lane_rate_info_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# %% [markdown]
# ## Everyday Winrate

# %%
hero_winrate_dict = dict()
ids = [h['id'] for h in id_to_name_dict_json['data']['constants']['heroes']]
hero_names = [h['displayName'] for h in id_to_name_dict_json['data']['constants']['heroes']]
for heroind, id in enumerate(tqdm(ids)):
    hname = hero_names[heroind]
    hero_winrate_dict[hname] = dict()
    url = f"https://stratz.com/heroes/{id}"
    hero_winrate_dict[hname]['url'] = url
    body="""
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
    headers= {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
          }
    response = requests.post(url="https://api.stratz.com/graphql", json={"query": body}, headers=headers)
    # print("response status code: ", response.status_code)
    if response.status_code != 200:
        print(f"GG, EVERYDAY WINRATE not equal 200 for {id} {hname}")
        break
    output_dict = json.loads(response.content.decode())
    win_counts = sum([h['winCount'] for h in output_dict['data']['heroStats']['winHour']])
    match_counts = sum([h['matchCount'] for h in output_dict['data']['heroStats']['winHour']])
    hero_winrate_dict[hname]['winrate'] = win_counts / match_counts

# sort the winrate dict
hero_winrate_dict = dict(sorted(hero_winrate_dict.items(), key=lambda item: item[1]['winrate'], reverse=True))

# %%
# save them 
with open("../records/hero_winrate_info_dict.pkl", 'wb') as f:
    pickle.dump(hero_winrate_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# save them to deployment env 
with open("../../dota_banpick/data/records/hero_winrate_info_dict.pkl", 'wb') as f:
    pickle.dump(hero_winrate_dict, f, protocol=pickle.HIGHEST_PROTOCOL)

# %%
# run the server 
subprocess.run(['bash', '/home/sukai/opt/run_banpick_website.sh'])

# %%



