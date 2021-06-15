import json
import pandas as pd

# Build insitutions dataframe
with open("device_author_data.json", "r") as f:
    auth_list = json.load(f)

location_dict = {"ID": [], "Location": [], "Year": []}

i = 1
for author in auth_list.values():
    if author["affiliation"] != []:
        inst = author["affiliation"]
        for item in inst:
            location_dict["ID"].append(i)
            location_dict["Location"].append(item[0])
            location_dict["Year"].append(eval(item[1]))
            i +=1

loc_df = pd.DataFrame.from_dict(location_dict)

loc_df.to_csv("./GIS/institution_years.csv", columns=["Year"], index_label="ID")

# Export unique location List
un_loc_df = loc_df.drop_duplicates("Location", ignore_index=True)
#loc_df.to_csv("Medical-Device-Project/GIS/institution_locations.csv")