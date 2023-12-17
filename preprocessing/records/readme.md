# Data structure

## Lane_rate_info_dict
```
dict[hero_name] = {
    'url' : url,
    'Pos 1 Pick Rate': num,
    'Pos 2 Pick Rate': num,
    'Pos 3 Pick Rate': num,
    'Pos 4 Pick Rate': num,
    'Pos 5 Pick Rate': num
}
```

## Url_name_dict
```
dict[hero_info_url] = hero_name
```

## winrate_matrix
```
dict[hero_name][opponent_hero_name] = num
```

## lanwin_dict
```
dict[hero_name][targ_hero_name] = score
```

## default pos hero pool
- these are in plain text format

## Hero_versus_with_winrate_dict (Deprecated)
```
dict[hero_name][paired_hero_name] = {
    'Versus Win Rate': num,
    'Match Win Rate': num
}

```

# Update Hero Stats Matrix
```bash
#!/bin/bash
conda activate dota
cd ./dota_banpick_project/preprocessing/notebook
python ./stratz_api_calling.py
```

# Other Important Notes

- if there are major patch updates (e.g., introducing new heroes), one need to manually update the following files 
  - `hero_abbrev.csv`
  - `heronames.csv`
  - `default_pos_x_hero_pool.txt`