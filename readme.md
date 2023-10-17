# DOTA 2 ban pick tool 
> [!WARNING]
> App not setup: This app is still in development mode 

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

## Deployment 
- Flask web app will be deployed. 

## Structure 
- Web scraping 

## Promise
- The banpick app will be updated to suit new patches as long as the authors still play DOTA 2 

