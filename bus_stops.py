import pandas as pd
import json

bus_stops = {}
xls = pd.ExcelFile(r'bus_stops_cleaned.xlsx')
for sheets in xls.sheet_names:
    data = pd.read_excel(r'bus_stops_cleaned.xlsx', sheet_name = sheets)
    df = pd.DataFrame(data)
    bus_stops[sheets] = df.to_dict()

bus_stops_json = json.dumps(bus_stops, indent = 8)
with open('bus_stops_cleaned.json', 'w') as outfile:
    outfile.write(bus_stops_json)