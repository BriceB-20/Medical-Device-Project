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
                                 "Query Key": med_dev_dom.find("./QueryKey").text}
'''
for item in med_dev_dom.iterfind("./IdList/Id"):
    search_info["medical device"]["PMIDs"].append(item.text)
'''

# Creates a new WebEnv for further searches and fetch request
WebEnv = "&WebEnv={}".format(med_dev_dom.find("./WebEnv").text)
WebEnv_raw = med_dev_dom.find("./WebEnv").text

# Fetch request construction

for article in search_info:
    for query_key in search_info[article]["Query Key"]:
        query_params = "{webenv}&query_key={key}".format(key=query_key, webenv=WebEnv)
        search_info[article]["Fetch URL"] = query_params

# Prints search info to json file for logs
search_info["a_comment"] = {"Date": str(datetime.datetime.now()),
                            "Web Environment String": WebEnv_raw}

with open(r"C:\Users\Briceno\PycharmProjects\Workspace\(Log)PubMed API Data Extraction.json", "w") as log:
    json.dump(search_info, fp=log, indent=6)
    log.close()

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

# Get DocSums from API
count = 2
for item in search_info:
    if item == "a_comment":  # Skips my comment data in the log
        continue
    retstart = 0
    retmax = 10000
    retrieval_params = "&retstart={retstart}&retmax={retmax}".format(retstart=str(retstart), retmax=str(retmax))
    print(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
    fetch_request = requests.get(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
    doc_sums = ElementTree.fromstring(fetch_request.content)

    time.sleep(.4)  # Avoids making more than 3 requests per second

    for article in doc_sums:
        pmuid = article.find("Id").text
        title = article.find('./Item[@Name="Title"]').text
        authors = ", ".join(author.text for author in article.find('./Item[@Name="AuthorList"]'))
        year = "".join(re.findall(r"\d{4}", article.find('./Item[@Name="PubDate"]').text))  # Only extract year
        journal = article.find('./Item[@Name="Source"]').text
        try:
            doi = article.find('./Item[@Name="DOI"]').text
        except AttributeError:
            doi = None
        query_key_output = search_info[item]["Fetch URL"][-1]

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

        print(count)
        count += 1

    # Construction of retstart/retmax iteration variables
    retstart += 10000
    retmax += 10000

    num_articles = int(search_info[item]["Count"])
    iter_check = num_articles - (count - 2)

    while iter_check > 0:  # trigger a retstart/retmax iteration if num obj exceed API limit
        retrieval_params = "&retstart={retstart}&retmax={retmax}".format(retstart=str(retstart), retmax=str(retmax))
        fetch_request = requests.get(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
        print(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
        doc_sums = ElementTree.fromstring(fetch_request.content)

        time.sleep(.4)

        for article in doc_sums:  # equivalent to med_dev_dom.iterfind("./DocSum")
            pmuid = article.find("Id").text
            title = article.find('./Item[@Name="Title"]').text
            authors = ", ".join(author.text for author in article.find('./Item[@Name="AuthorList"]'))
            year = "".join(re.findall(r"\d{4}", article.find('./Item[@Name="PubDate"]').text))
            journal = article.find('./Item[@Name="Source"]').text
            try:
                doi = article.find('./Item[@Name="DOI"]').text
            except AttributeError:
                doi = None
            query_key_output = search_info[item]["Fetch URL"][-1]

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

            print(count)
            count += 1

        retstart += 10000
        retmax += 10000
        iter_check = num_articles - (count - 2)

data_output.save(r"C:\Users\Briceno\Desktop\pubmed_API_output.xlsx")
data_output.close()
