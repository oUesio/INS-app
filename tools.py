import numpy as np
import csv

def export_csv(csv_name, data):
    with open(csv_name+'.csv', "w") as outfile:
        dict_writer = csv.DictWriter(outfile, data[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(data)
