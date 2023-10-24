# DOTA 2 ban pick tool 
> [!WARNING]
> The app is in alpha version, which doesn't always have the full features implemented. 

## Quickstart
### Install at your local machine
1. you shall have a python 3.10 environment 
   - if you have anaconda, then simply setup a conda env by run `conda create -y --name dota python=3.10 && conda activate dota`
   - Otherwise, go to [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html) to download python environment
2. to install the app, open a terminal with python environment, run `pip install "https://github.com/Sino-Huang/DOTA-2-ban-pick-tool/archive/master.zip"`
3. after install the python package, simply run `dota-banpick` in your terminal to start the app!
### Try our web app
> [!IMPORTANT]
> We may shutdown our web server at any time due to budget. 

Go to https://www.banpick.win/ to try our app!

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/huangsukaig)

### How to use demo 
Go to [Youtube Video Demo](https://youtu.be/krG0LuIItCw) to know how to use the tool.

## Purpose 
- User friendly and newbee friendly DOTA 2 ban pick tool. 
- Help you and your friends to drafting 

## Related Work 
- Most existing tools are outdated (e.g., http://dotapicker.com)
- Most existing tools are not practical. (e.g., picking two middle heros to counter the opponent)

## Pipeline 
- we will pre-define hero pool for position 1 - 5. (users can modify it though)
- users need to define your own hero pool and your position (this info can be saved and pass around)
- In the ban pick period, the tool will help you and your team to pick heros with the highest advantages 
  - there will be no collisions in the position 
  - hero combo will be also considered in addition to hero counter
  - specialised for All Pick mode
    - first round: 
      - pos 4 5 pick
      - pos 4 3 pick
      - pos 5 3 pick


## Algorithm 
- objective: greedy winrate maximization 
  - the advantage value will be the sum of the hero's winrate versus the opponents plus the winrate with allies, the weight for versus advantage varies as follows: 
  - tuning versus advantage weight:
    - mid should focus more on countering mid
    - pos 1 should focus more on countering pos 3 and then pos 1
    - pos 3 should focus more on countering pos 1 and then pos 2
    - pos 4 should focus more on countering pos 1 and pos 2
    - pos 5 should focus more on countering pos 3 
- alpha beta pruning 
  - find the optimal solution under the assumption that the opponents are also trying their hard to do the hero drafting

## UI
- similar to https://www.opendota.com/combos but also add ban button as well as the position flag
- so far, we have created a streamlit version.
- In the future, we will create a more interactive UI

## Deployment 
- So far, this app can only be deployed localy using Streamlit framework
- In the future, we will reconstruct the app using Django and deploy it online, please wait for us ~ 💖

## Structure 
```
.
├── 1_🎃_Homepage.py
├── alphabeta.py
├── config.py
├── data
│   ├── hero_wide_icons
│   └── records
├── heuristic.py
├── __init__.py
├── pages
│   ├── 2_🐻_Heroes.py
│   ├── 3_🌊_Edit_Hero_Pool.py
│   └── 4_🤕_BanPick.py
├── pickaction.py
└── utils.py
```

## Promise
- The banpick app will be updated to suit new patches as long as the authors still play DOTA 2 

## Legitimacy and Fair Play
1. No Cheating Involved:
  - Our tool is fundamentally different from real-time game-enhancing applications like Overwolf. It does not interact with the DOTA 2 game client or servers during gameplay nor does it parse player information in real-time.

2. Purely a Drafting Aid:
  - This tool is designed to serve as a drafting practice tool. Its sole purpose is to assist players in understanding and strategizing around the drafting phase of the game. It simulates various drafting scenarios to help players make informed decisions on hero selections and bans based on predefined metrics and algorithms.

3. No Real-Time Assistance:
  - The DOTA 2 Ban Pick Tool does not provide any real-time assistance, insights, or advantages during actual gameplay. It operates exclusively outside the game environment, thus preserving the game's competitive integrity.

4. No Data Parsing:
  - Unlike some other tools, our application does not parse or analyze player data during game runtime. It strictly operates based on predefined hero pools and user inputs prior to engaging in a game.

5. Privacy Respected:
  - We highly respect user privacy and game ethics. No personal or game data is accessed, collected, or shared through the use of this tool.