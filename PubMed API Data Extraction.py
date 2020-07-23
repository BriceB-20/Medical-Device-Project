import sqlite3
import requests
import xml.etree.ElementTree as ElementTree
import json
import openpyxl
import time
import re
import datetime

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
WebEnv_raw = med_dev_dom.find("./WebEnv").text

# Prints search info to json file for logs
search_info["_comment"] = {"Date": str(datetime.datetime.now()),
                           "Web Environment String": WebEnv_raw}

with open(r"C:\Users\Briceno\PycharmProjects\Workspace\(Log)PubMed API Data Extraction.json", "w") as log:
    json.dump(search_info, fp=log, indent=6)
log.close()

# Fetch request construction
fetch_url_query_list = []

for item in search_info:
    for query_key in search_info[item]["Query Key"]:
        query_params = "{webenv}&query_key={key}".format(key=query_key, webenv=WebEnv)
        fetch_url_query_list.append(query_params)

# Create workbook to output data
data_output = openpyxl.Workbook()
data_sheet = data_output["Sheet"]
data_sheet.title = "Data"

# Labels
header_list = ["PMUID", "Title", "Authors", "Year", "Journal", "DOI", "Query Key"]
column_letters = ["a", "b", "c", "d", "e", "f", "g"]

for header in header_list:
    letter_index = header_list.index(header)
    cell = "{}1".format(column_letters[letter_index].upper())
    data_sheet[cell] = header

data_sheet["H1"] = str(datetime.datetime.now())  # For record keeping purposes
data_sheet["H2"] = WebEnv_raw

# Get document summaries
count = 2
for fetch_url in fetch_url_query_list:
    fetch_request = requests.get(base_ESummary + fetch_url)
    doc_sums = ElementTree.fromstring(fetch_request.content)

    time.sleep(.4)  # Avoids making more than 3 requests per second

    for item in doc_sums:  # equivalent to med_dev_dom.iterfind("./DocSum")
        pmuid = item.find("Id").text
        title = item.find('./Item[@Name="Title"]').text
        authors = ", ".join(author.text for author in item.find('./Item[@Name="AuthorList"]'))
        year = re.findall(r"\d{4}", item.find('./Item[@Name="PubDate"]').text)  # Only extract year
        journal = item.find('./Item[@Name="Source"]').text
        doi = item.find('./Item[@Name="DOI"]').text
        query_key_output = fetch_url[-1]

        a_column, b_column, c_column, d_column, e_column, f_column, g_column = "A{}".format(str(count)),\
                                                                               "B{}".format(str(count)),\
                                                                               "C{}".format(str(count)),\
                                                                               "D{}".format(str(count)),\
                                                                               "E{}".format(str(count)),\
                                                                               "F{}".format(str(count)),\
                                                                               "G{}".format(str(count))
        data_sheet[a_column] = pmuid
        data_sheet[b_column] = title
        data_sheet[c_column] = authors
        data_sheet[d_column] = year
        data_sheet[e_column] = journal
        data_sheet[f_column] = doi
        data_sheet[g_column] = query_key_output

        count += 1

    retstart = 10000
    retmax = 20000

    while count >= 10002:  # trigger a retstart/retmax iteration if num obj exceed API limit
        retrieval_params = "&retstart={retstart}&retmax={retmax}".format(retstart=str(retstart), retmax=str(retmax))

        fetch_request = requests.get(base_ESummary + retrieval_params + fetch_url)
        doc_sums = ElementTree.fromstring(fetch_request.content)

        time.sleep(.4)

        for item in doc_sums:
            pmuid = item.find("Id").text
            title = item.find('./Item[@Name="Title"]').text
            authors = ", ".join(author.text for author in item.find('./Item[@Name="AuthorList"]'))
            year = re.findall(r"\d{4}", item.find('./Item[@Name="PubDate"]').text)  # Only extract year
            journal = item.find('./Item[@Name="Source"]').text
            doi = item.find('./Item[@Name="DOI"]').text
            query_key_output = fetch_url[-1]

                a_column, b_column, c_column, d_column, e_column, f_column, g_column = "A{}".format(str(count)), \
                                                                                       "B{}".format(str(count)), \
                                                                                       "C{}".format(str(count)), \
                                                                                       "D{}".format(str(count)), \
                                                                                       "E{}".format(str(count)), \
                                                                                       "F{}".format(str(count)), \
                                                                                       "G{}".format(str(count))
                data_sheet[a_column] = pmuid
                data_sheet[b_column] = title
                data_sheet[c_column] = authors
                data_sheet[d_column] = year
                data_sheet[e_column] = journal
                data_sheet[f_column] = doi
                data_sheet[g_column] = query_key_output

                count += 1

        retstart += 10000
        retmax += 10000

        if count ==  # Find a way to break the while loop. Keep everything in search_info so can reference count.

data_output.save(r"C:\Users\Briceno\Desktop\pubmed_API_output.xlsx")
data_output.close()
