import numpy as np
import pandas as pd
import openpyxl as xl
import re
from matplotlib import pyplot as plt

data = {}

# Extract data on number of publication per year
wb = xl.load_workbook(filename=r"C:\Users\Briceno\Desktop\pubmed_API_output.xlsx")
data_sheet = wb["Data"]

count = 2
for i in range(2, data_sheet.max_row):
    pos = "D{}".format(str(i))
    cell = data_sheet[pos]

    if re.match(r"\d{5}", cell.value) is not None:  # Eliminates aberrant years. E.g. '20042005'
        continue
    if int(cell.value) in data:
        data[int(cell.value)] += 1
    else:
        data[int(cell.value)] = 1

wb.close()
data = dict(sorted(data.items()))

data_frame = pd.DataFrame.from_dict(data=data, orient="index")

plt.plot(data_frame)
plt.show()
