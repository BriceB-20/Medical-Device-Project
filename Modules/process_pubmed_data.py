import re
import json
import datetime # needed for eval() function
import pandas as pd
from fuzzywuzzy import process,fuzz


def get_author_info(pubmed_data_df, cutoff_year, write_file_name):
    '''
    Create author info json file from raw pubmed extraction json file
    '''
    identifier_list = {}
    id_count = 1

    # Create data structure for author
    for i, paper in enumerate(pubmed_data_df["Authors"]):
        for author in paper:
            if author["name"] != None and eval(pubmed_data_df["Date"][i]).year <= cutoff_year:
                
                # If author is already in the dictionary
                if author["name"].lower() in identifier_list.keys():

                    # Update Values
                    identifier_list[author["name"].lower()]["weight"] += 1
                    identifier_list[author["name"].lower()]["years active"].append(pubmed_data_df["Date"][i])      

                # If the author is not already in the dictionary
                else:
                    identifier_list[author["name"].lower()]  = {"id": id_count, 
                                                        "years active":[pubmed_data_df["Date"][i]], 
                                                        "affiliation":[], "weight": 1, "edges":[]}

                # Get year/affiliation data for GIS
                if author["affiliation"] != None:
                    aff = author["affiliation"]
                    aff = re.sub(r"[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+", "", aff)  # Remove emails. Some authors only list email.
                    aff = re.sub(r"(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!@:%_\+.~#?&\/\/=]*)", "", aff)  # Remove websites
                    aff = aff.strip(" ")
                    if aff != "":  # Skips authors who only put an email as thier insitution
                        identifier_list[author["name"].lower()]["affiliation"].append((aff, pubmed_data_df["Date"][i]))

                # Append other authors to edges list
                temp_list = [[o_author["name"].lower(), 0, pubmed_data_df["Date"][i]] for o_author in paper]  # Zero holds place for co-author ID
                for item in temp_list:
                    if item[0] != author["name"].lower():
                        identifier_list[author["name"].lower()]["edges"].append(item)
                
                id_count +=1
                
    # Get author id for co-authors
    for author in identifier_list:
        for item in identifier_list[author]["edges"]:
            if item[0] in identifier_list.keys():
                item[1] = identifier_list[item[0]]["id"]

            
    with open(write_file_name, "w") as f:
        json.dump(identifier_list, f, indent=4)



def match_affiliation(author_data, min_ratio, write_file_name):
    '''
    Clean author insitituitonal affiliations using fuzzy matching
    '''
    full_list = [] 
    for author in author_data: # Extract all listed institutions
        for item in author_data[author]["affiliation"]:
            full_list.append(item[0])

    full_list = (set(full_list)) # Get unique items 
    reducing_list = full_list.copy()
    already_categorized = []
    similarity_groups = []

    for insitituiton in full_list:
        if insitituiton not in already_categorized:
            group = [insitituiton]
            already_categorized.append(insitituiton)
            ratios = process.extract(insitituiton, reducing_list, scorer=fuzz.token_sort_ratio)  # Can tweek the scorer used
            for inst_ratio in ratios:
                if inst_ratio[0] != insitituiton and inst_ratio[1] > min_ratio:
                    group.append(inst_ratio[0])
                    already_categorized.append(inst_ratio[0])
                    reducing_list.remove(inst_ratio[0])
            similarity_groups.append(group)
    
    # Save groups to JSON
    group_dict_by_id = {i:keys for i,keys in enumerate(similarity_groups)}
    with open(write_file_name, "w") as f:
        json.dump(group_dict_by_id, f, indent=4)
    print("Groups Saved")


def create_df(file_path, clean_years=True, cutoff_year=2000, remove_errors=False):
    '''
    Convert JSON from pubmed import into a pandas dataframe
    '''
    with open(file_path, "r") as f:
        full_dict = json.load(f)
    
    # slim_dict = {key:value for (key, value) in full_dict.items() if key in ["Pubmed ID", "Title", "Journal", "Date"]}
    df = pd.DataFrame.from_dict(full_dict)
    if remove_errors:
        df = df[df["Pubmed ID"] != "000"]  # Removes data with parsing error
    
    # Cleaning years
    if clean_years:
        df["Date"] = df["Date"].apply(lambda x : eval(x).year)  # Converts date from __repr__ format
        for index in df.loc[df["Date"] > cutoff_year].index:
            df.drop([index], inplace=True)
    
    return df