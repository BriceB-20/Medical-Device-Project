import sqlite3
import requests
import xml.etree.ElementTree as ElementTree
import json
import openpyxl
import time

search_info = {}

# Bases
base_ESearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
base_ESummary = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed"

# Searches
med_dev_search = '&term="medical+device"+OR+"medical+devices"&field=title/abstract&usehistory=y'

# Initial search
med_dev_dom = requests.get(base_ESearch + med_dev_search)
med_dev_dom = ElementTree.fromstring(med_dev_dom.content)  # med_dev_dom is now the root object

search_info["medical device"] = {"Count": med_dev_dom.find("./Count").text,
                                 "Query Key": med_dev_dom.find("./QueryKey").text,
                                 "PMIDs": []}

for item in med_dev_dom.iterfind("./IdList/Id"):
    search_info["medical device"]["PMIDs"].append(item.text)

# Creates a new WebEnv for further searches and fetch request
WebEnv = "&WebEnv={}".format(med_dev_dom.find("./WebEnv").text)

# Prints search info to text file for logs
with open(r"C:\Users\Briceno\PycharmProjects\Workspace\(Log)PubMed API Data Extraction.json", "w") as log:
    log.write("Web Environment String: " + WebEnv)
    log.write("\n")
    json.dump(search_info, fp=log, indent=4)
log.close()

# Fetch request construction
fetch_url_query_list = []
for item in search_info:
    for query_key in search_info[item]["Query Key"]:
        "&WebEnv={webenv}&retmode=json&query_key={key}".format(key=query_key, webenv=WebEnv)

# Create workbook to output data
with openpyxl.Workbook() as data_output:
    data_sheet = data_output["Sheet"]
    data_sheet.title = "Data"

    # Labels
    header_list = ["PMUID", "Title", "Authors", "Date", "Journal", "DOI", "Query Key"]

# Get document summaries
for fetch_url in fetch_url_query_list:
    fetch_request = requests.get(base_ESummary + fetch_url)
    doc_sums = json.loads(fetch_request.content)

    time.sleep(.4)  # Avoids making more than 3 requests per second

    for item in doc_sums["results"]:
        if item == doc_sums["results"]["uids"]:
            continue
        else:
            query_key_output = fetch_url[-1]

    if len(doc_sums["results"].keys()) > 9999:  # trigger a retstart/retstart iteration if num obj exceed API limit
        pass

data_output.save(r"C:\Users\Briceno\Desktop\pubmed_API_output.xlsx")
data_output.close()
