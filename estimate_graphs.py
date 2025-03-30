import tools
import os
import pandas as pd
import numpy as np

directory = 'results/estimates'
for filename in sorted(os.listdir(directory)):
    if ("walk_trial" in filename or "run_trial" in filename or "stairs_trial" in filename or "mixed_trial" in filename) and filename.endswith(".csv"):  # Filter relevant CSV files
        file_path = os.path.join(directory, filename)
        print (filename)
        data = np.loadtxt(file_path, delimiter=",", skiprows=1)
        positions = data[:, :3]
        zv = data[:, -1].astype(bool)

        name = filename.replace('.csv', '')
        parts = [x for x in name.split('_') if x != "hallway"]

        tools.save_topdown(positions, zv, parts[1], parts[0], f'results/graphs/{name}_topdown.png')
        tools.save_vertical(positions, zv, parts[1], parts[0], f'results/graphs/{name}_vertical.png')
