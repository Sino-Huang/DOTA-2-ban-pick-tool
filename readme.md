# DOTA 2 ban pick tool 

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


## Algorithm 
- advantage maximization 
- alpha beta pruning (future work)

## Deployment 
- Flask web app will be deployed. 

## Structure 
- Web scraping 

## Promise
- The banpick app will be updated to suit new patches as long as the authors still play DOTA 2 