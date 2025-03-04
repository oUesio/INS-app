import glob
import os 
from decimal import Decimal
from tools import calc_dist

det = 'shoe'

trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
approx = False ####
estim = True ####
freq = 1/100

threshold = 2.2e8
window = 5
sig_a = 0.00098
sig_w = 9.2e-5
sig_vel = 0.005
acc = 0.3
gyr = 1


files = glob.glob('data/hallway/walk/*.csv')
remove = ['data/hallway/walk/exportfile.csv', 'data/hallway/walk/exportfileMAIN.csv', 'data/hallway/walk/exportfiletest.csv']
files = [os.path.basename(x).replace('.csv', '') for x in files if x not in remove]

file_dists = dict.fromkeys(files, None)

for filename in files:
    file_dists[filename] = calc_dist(det, window, threshold, trial_type, trial_speed, filename, freq, sig_a, sig_w, sig_vel, acc, gyr)

print (file_dists)