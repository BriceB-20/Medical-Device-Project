import json
import datetime
from pymed import PubMed
import pandas as pd

'''
Pubmed Query Builder: https://pubmed.ncbi.nlm.nih.gov/advanced/

### MeSH Terms of Note
* Biomedical Engineering 
* Biomedical Technology
* Equipment Safety
* Equipment Design
* Prostheses and Implants

### Formatting Notes
* Dates stored in __repr__ format in JSON
* 000 = Code for unobtainable PMUID
'''

# Uses Pymed to get results for the desired query
def search(query_string, pubmed_module, max_results=2000):
    results = pubmed_module.query(query_string, max_results=max_results)
    return results

# Gets relevant data from Pymed iterable and creates a dictionary
def pubmed_todict(pubmed_iterable):
    new_dict = {"Result Number": [], "Pubmed ID": [], "Title": [], "Abstract":[], "Journal": [], "Authors": [], "Date": []}
    
    # Assemble dictionary
    for i, article in enumerate(pubmed_iterable):
        new_dict["Result Number"].append(i)
        if "\n" in article.pubmed_id:  # Deals with parsing issue for article PMUID
            new_dict["Pubmed ID"].append("000")
        else:
            new_dict["Pubmed ID"].append(article.pubmed_id)   
        new_dict["Title"].append(article.title)
        new_dict["Abstract"].append(article.abstract)
        try:  # Deals with books and book reviews (rather than articles) in the database
            new_dict["Journal"].append(article.journal)
        except AttributeError:
            new_dict["Journal"].append("Book") 
        new_dict["Authors"].append(article.authors)
        if type(article.publication_date) == datetime.date:  # Standardizes data. Pymed returns some years as int
            new_dict["Date"].append(article.publication_date) 
        else:
            new_dict["Date"].append(datetime.datetime.strptime(str(article.publication_date), "%Y"))
        
    # Cleans author data
    clean_author_list_by_paper = []
    for paper_author_list in new_dict["Authors"]:
        if paper_author_list == []:
            clean_author_list_by_paper.append([{"name": None, "affiliation": None}])
        else:
            author_list_by_paper = []
            for author in paper_author_list:
                if author["lastname"] != None or author["initials"] != None:
                    try:
                        author_dict = {"name": "{} {}".format(author["lastname"], author["initials"]),
                                "affiliation": author["affiliation"]}
                    except KeyError:
                        author_dict = {"name": "{} {}".format(author["lastname"], author["initials"]),
                                    "affiliation": None}
                    author_list_by_paper.append(author_dict)
            clean_author_list_by_paper.append(author_list_by_paper)
    
    new_dict["Authors"] = clean_author_list_by_paper
    
    return new_dict

# Avoids serialization error with datetime in JSON dump
# See https://stackoverflow.com/questions/54557568/typeerror-object-of-type-date-is-not-json-serializable
def datetime_converter(object):
    if isinstance(object, datetime.date):
        return object.__repr__()


def search_and_dump(query_string, max_results, file_name, create_json):
    '''
    Uses PyMed to return PubMed results for a given query string in JSON or pandas table format
    '''
    pubmed = PubMed(tool="Medical Device Author Network Analysis", email="bowrey@umd.edu")
    results = search(query_string=query_string, pubmed_module=pubmed, max_results=max_results)
    new_dict = pubmed_todict(pubmed_iterable=results)
    if create_json is True:
        with open("JSON Data\{}".format(file_name), "w") as f:
            # Default argument takes function that is called when JSON ecounters object it can't convert
            json.dump(new_dict, f, indent=4, default=datetime_converter)
            print("Search Completed. File dumped to JSON")
    else:
        return pd.DataFrame.from_dict(new_dict)