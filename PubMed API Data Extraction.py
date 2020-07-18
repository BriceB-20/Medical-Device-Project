import sqlite3
import requests
import xml.etree.ElementTree as ElementTree
import json

query_keys = []
search_info = {}

# Bases
base_ESearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Searches
med_dev_search = '?db=pubmed&term="medical+device"+OR+"medical+devices"&field=title/abstract&usehistory=y'

# Initial search
med_dev_dom = requests.get(base_ESearch + med_dev_search)
med_dev_dom = ElementTree.fromstring(med_dev_dom.content)  # med_dev_dom is now the root object

search_info["medical device"] = {"Count": med_dev_dom.find("./Count").text,
                                 "Query Key": med_dev_dom.find("./QueryKey").text,
                                 "PMIDs": []}

for item in med_dev_dom.iterfind("./IdList/Id"):
    search_info["medical device"]["PMIDs"].append(item.text)

# Creates a new WebEnv for further searches
WebEnv = "&WebEnv={}".format(med_dev_dom.find("./WebEnv").text)

# Prints info to text file for logs
with open(r"C:\Users\Briceno\PycharmProjects\Workspace\(Log)PubMed API Data Extraction.json", "w") as log:
    log.write("Web Environment String: " + WebEnv)
    log.write("\n")
    json.dump(search_info, fp=log, indent=4)
log.close()

# Testing




