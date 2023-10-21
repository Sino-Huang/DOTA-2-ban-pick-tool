# Data structure
## Hero_versus_with_winrate_dict
```
dict[hero_name][paired_hero_name] = {
    'Versus Win Rate': num,
    'Match Win Rate': num
}

```

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

## default pos hero pool
- these are in plain text format