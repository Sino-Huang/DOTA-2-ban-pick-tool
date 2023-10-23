import pickle
import pandas as pd

if __name__ == "__main__":
    df = pd.read_csv("../records/heronames.csv",  header=None,)
    df.columns = ["Name", "Image filename", "Type"]
    new_df = pd.DataFrame(df['Name'])
    abbrev_list = []
    for name in new_df['Name']:
        i = input(f"abbrev for {name}")
        abbrev_list.append(i)
        
    new_df['Chinese Abbrev'] = abbrev_list
    
    new_df.to_csv("../records/hero_chinese_abbrev.csv", index=False)
    