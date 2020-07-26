import requests
import xml.etree.ElementTree as ElementTree
import json
import openpyxl
import time
import re
import datetime

WebEnv = ""
WebEnv_raw = ""
search_info = {}


def search(search_query, inner_search_description, create_web_env=False):
    global WebEnv
    global WebEnv_raw
    dom = requests.get(base_ESearch + search_query + WebEnv)  # After initial search, there will be a WebEnv to concat
    dom = ElementTree.fromstring(dom.content)  # med_dev_dom is now the root object

    search_info[inner_search_description] = {"Count": dom.find("./Count").text,
                                             "Query Key": dom.find("./QueryKey").text}

    # Creates a new WebEnv based on initial search for further searches and fetch request
    if create_web_env is True:
        WebEnv = "&WebEnv={}".format(dom.find("./WebEnv").text)
        WebEnv_raw = dom.find("./WebEnv").text


def scrape_and_output(inner_article, inner_search_info, inner_data_sheet):
    global count
    pm_uid = inner_article.find("Id").text
    title = inner_article.find('./Item[@Name="Title"]').text
    authors = ", ".join(author.text for author in inner_article.find('./Item[@Name="AuthorList"]'))
    year = "".join(re.findall(r"\d{4}", inner_article.find('./Item[@Name="PubDate"]').text))  # Only extract year
    journal = inner_article.find('./Item[@Name="Source"]').text
    try:
        doi = inner_article.find('./Item[@Name="DOI"]').text
    except AttributeError:
        doi = None
    query_key_output = inner_search_info[item]["Fetch URL"][-1]

    a_column, b_column, c_column, d_column, e_column, f_column, g_column = "A{}".format(str(count)), \
                                                                           "B{}".format(str(count)), \
                                                                           "C{}".format(str(count)), \
                                                                           "D{}".format(str(count)), \
                                                                           "E{}".format(str(count)), \
                                                                           "F{}".format(str(count)), \
                                                                           "G{}".format(str(count))
    inner_data_sheet[a_column] = pm_uid
    inner_data_sheet[b_column] = title
    inner_data_sheet[c_column] = authors
    inner_data_sheet[d_column] = year
    inner_data_sheet[e_column] = journal
    inner_data_sheet[f_column] = doi
    inner_data_sheet[g_column] = query_key_output

    print(count)
    count += 1


# Bases
base_ESearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
base_ESummary = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed"

# Initial search
med_dev_search = '&term="medical+device"+OR+"medical+devices"&field=title/abstract&usehistory=y'
search(search_query=med_dev_search, inner_search_description="medical device", create_web_env=True)

# Other searches

# Fetch request construction
for search_description in search_info:
    for query_key in search_info[search_description]["Query Key"]:
        query_params = "{webenv}&query_key={key}".format(key=query_key, webenv=WebEnv)
        search_info[search_description]["Fetch URL"] = query_params

# Prints search info to json file for logs
search_info["_comment"] = {"Date": str(datetime.datetime.now()),
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
retstart = 0
retmax = 10000

for item in search_info:
    if item == "_comment":  # Skips my comment data in the log
        continue

    retrieval_params = "&retstart={retstart}&retmax={retmax}".format(retstart=str(retstart), retmax=str(retmax))
    print(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])

    fetch_request = requests.get(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
    doc_sums = ElementTree.fromstring(fetch_request.content)

    time.sleep(.4)  # Avoids making more than 3 requests per second

    for article in doc_sums:
        scrape_and_output(inner_article=article, inner_search_info=search_info, inner_data_sheet=data_sheet)

    retstart += 10000
    retmax += 10000

    # Construction of retstart/retmax iteration variables
    num_articles = int(search_info[item]["Count"])
    iter_check = num_articles - (count - 2)

    while iter_check > 0:  # trigger a retstart/retmax iteration if num obj exceed API limit of 10000 items
        retrieval_params = "&retstart={retstart}&retmax={retmax}".format(retstart=str(retstart), retmax=str(retmax))
        fetch_request = requests.get(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
        print(base_ESummary + retrieval_params + search_info[item]["Fetch URL"])
        doc_sums = ElementTree.fromstring(fetch_request.content)

        time.sleep(.4)

        for article in doc_sums:
            scrape_and_output(inner_article=article, inner_search_info=search_info, inner_data_sheet=data_sheet)

        retstart += 10000
        retmax += 10000
        iter_check = num_articles - (count - 2)

data_output.save(r"C:\Users\Briceno\Desktop\pubmed_API_output.xlsx")
data_output.close()
