import glob
import os 
from decimal import Decimal
from tools import calc_dist
import json

import numpy as np


'''thresholds = [2e8] # 2e8
windows = [5] # 5
sig_a = [0.00098] # 0.00098
sig_w = [8.7266463e-5] # 8.7266463e-5
sig_vel = [0.01] # 0.01
accs = [0.5, 1] # 0.5
gyrs = [0.5, 1] # 0.5'''


det = 'shoe'
trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
freq = 1/100

'''thresholds = [1e8, 4e8, 6e8] # 2e8
windows = [5] # 5
sig_a = [0.007, 0.01] # 0.00098
sig_w = [5.2e-5, 0.01*np.pi/180] # 8.7266463e-5
sig_vel = [0.0007, 0.01, 0.05] # 0.01
accs = [0.2, 0.5, 1, 1.5] # 0.5
gyrs = [0.2, 0.5, 1, 1.5] # 0.5'''

'''thresholds = [9.5e5, 1.5e6, 3.5e6] # 2e8
windows = [5] # 5
sig_a = [0.035234433782004124] # 0.00098
sig_w = [0.0008884048317068069] # 8.7266463e-5
sig_vel = [0.005, 0.01, 0.015] # 0.01
accs = [0.3, 0.5, 1] # 0.5
gyrs = [0.3, 0.5, 1] # 0.5
'''

thresholds = [1.8e8, 2e8, 2.2e8] # 2e8
windows = [5] # 5
sig_a = [0.00098, 0.00105] # 0.00098 
sig_w = [8.7266463e-5, 9.2e-5] # 8.7266463e-5
sig_vel = [0.005, 0.01, 0.015] # 0.01
accs = [0.3, 0.5, 1] # 0.5
gyrs = [0.3, 0.5, 1] # 0.5

try:
    with open("test_optimal/dists.json", "r") as file:
        data = json.load(file)  # Load existing dictionary
except FileNotFoundError:
    data = {} 

# {params: {exportfile: 0, exportfile2: 0, ...}, params2: {exportfile: 0, exportfile2: 0, ...}, ...}

files = glob.glob('data/hallway/walk/*.csv')
remove = ['data/hallway/walk/stationary.csv', 'data/hallway/walk/stationary1.csv', 'data/hallway/walk/exportfile.csv', 'data/hallway/walk/exportfileMAIN.csv', 'data/hallway/walk/exportfiletest.csv']
files = [os.path.basename(x).replace('.csv', '') for x in files if x not in remove]

for thresh in thresholds:
    for win in windows:
        for a in sig_a:
            for w in sig_w:
                for vel in sig_vel:
                    for acc in accs:
                        for gyr in gyrs:
                            # all params gotten
                            p = '_'.join(['%.2E' % Decimal(thresh),str(win),str(a),'%.2E' % Decimal(w),str(vel),str(acc),str(gyr)])
                            results = {}
                            if p not in data: # doesnt recalc if already in
                                params = {}
                                for filename in files:
                                    dist = calc_dist(det, win, thresh, trial_type, trial_speed, filename, freq, a, w, vel, acc, gyr)
                                    results[filename] = dist
                                print (p)
                                params[p] = results
                                data.update(params) # update everytime
                                with open("test_optimal/dists.json", "w") as file:
                                    json.dump(data, file, indent=4)

# functionality to use params and gets the best stuff
best_avg_param = [None, -1] # param, best average
best_file_param = dict.fromkeys(files, [None, -1]) # keys: filename, []: param, distance

for param in data:
    vals = data[param].values() # [floats]
    avg = sum(vals) / len(vals)
    if best_avg_param[1] == -1 or best_avg_param[1] > avg:
        best_avg_param = [param, avg]
    for filename in best_file_param:
        if best_file_param[filename][1] == -1 or best_file_param[filename][1] > data[param][filename]:
            best_file_param[filename] = [param, data[param][filename]]

with open("test_optimal/best_dists.json", "w") as file:
    json.dump({**{"BEST_AVG_PARAMS": best_avg_param}, **best_file_param}, file, indent=4)

print ('==================')
print (best_avg_param)
print (best_file_param)
print ('==================')
print ('Best average params')
print (best_avg_param[0]+': '+str(best_avg_param[1]))
print ('')
for filename in best_file_param:
    print ('Best params for '+filename)
    print (best_file_param[filename][0]+': '+str(best_file_param[filename][1]))



'''
thresholds = [1.8e8, 2e8, 2.2e8] # 2e8
windows = [5] # 5
sig_a = [0.007] # 0.00098
sig_w = [5.2e-5] # 8.7266463e-5
sig_vel = [0.0007] # 0.01
accs = [0.3, 0.5, 1] # 0.5
gyrs = [0.3, 0.5, 1] # 0.5


thresholds = [1.8e8, 2e8, 2.2e8] # 2e8
windows = [5, 7] # 5
sig_a = [0.00098, 0.00105] #
sig_w = [9.2e-5] # 8.7266463e-5
sig_vel = [0.005, 0.01, 0.015] # 0.01
accs = [0.3, 0.5, 1] # 0.5
gyrs = [0.3, 0.5, 1] # 0.5

'''