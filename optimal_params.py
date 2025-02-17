import glob
import os 
from ins_tools.util import *
from ins_tools.INS import INS

from decimal import Decimal

def calc_dist(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro):# approx, estim):
    # Gets the imu data from csv file
    with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'), mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro) #microstrain
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    x = ins.baseline(zv=zv)

    #print (x[-1, :3])
    return np.linalg.norm(x[-1,:3]) # distance between final point and # CHANGE THIS, DONT ACCOUNT FOR VERTICAL DIST TEMP FOR WALKING ON FLAT

thresholds = [2e8] # 2e8
windows = [5] # 5
sig_a = [0.00098] # 0.00098
sig_w = [8.7266463e-5] # 8.7266463e-5
sig_vel = [0.01] # 0.01
accs = [0.5, 1] # 0.5
gyrs = [0.5, 1] # 0.5


det = 'shoe'
trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
freq = 1/100

'''thresholds = [1.8e8, 2e8, 2.2e8] # 2e8
windows = [5, 7] # 5
sig_a = [0.00098, 0.00105] # 0.00098
sig_w = [8.7266463e-5, 9.2e-5] # 8.7266463e-5
sig_vel = [0.01, 0.015] # 0.01
accs = [0.5, 1] # 0.5
gyrs = [0.5, 1] # 0.5'''
'''
['2.20E+08_5_0.00098_9.20E-05_0.01_1_0.5', 1.835374314525408]
{'exportfile_SHOEREVNORMLOOONG2': ['2.00E+08_5_0.00098_9.20E-05_0.015_1_0.5', 2.5476763497150543], 
'exportfileLONG_REV2': ['2.20E+08_5_0.00098_9.20E-05_0.01_1_0.5', 1.4625492727660414], 
'exportfileLONG2': ['2.20E+08_5_0.00098_9.20E-05_0.01_1_1', 1.620208417615325], 
'exportfile_SHOEREV': ['2.00E+08_5_0.00098_9.20E-05_0.01_1_1', 0.916859447694411], 
'exportfile_SHOELOOONG2': ['2.20E+08_5_0.00098_9.20E-05_0.01_1_0.5', 2.7733554987671023], 
'exportfileLONG_REV': ['1.80E+08_7_0.00098_9.20E-05_0.01_1_0.5', 1.330152551755503], 
'exportfile_SHOENORMLOOONG2': ['1.80E+08_5_0.00098_8.73E-05_0.015_1_0.5', 3.149591244253708], 
'exportfile_SHOE2': ['2.20E+08_5_0.00098_9.20E-05_0.01_1_0.5', 1.8932855998823854], 
'exportfile_SHOE': ['1.80E+08_7_0.00105_9.20E-05_0.01_0.5_1', 1.6139667229147385], 
'exportfileLONG': ['2.20E+08_5_0.00098_9.20E-05_0.01_1_1', 1.3491774646474732], 
'exportfile_SHOEREVLOOONG': ['2.20E+08_7_0.00105_9.20E-05_0.01_1_0.5', 1.240086524826173], 
'exportfile_SHOEREVNORM': ['2.20E+08_5_0.00098_9.20E-05_0.015_1_0.5', 0.6662542630989314], 
'exportfile_SHOELOOONG': ['1.80E+08_7_0.00098_8.73E-05_0.01_1_0.5', 1.643176057668135], 
'exportfile_SHOENORMLOOONG': ['1.80E+08_7_0.00098_8.73E-05_0.015_1_0.5', 2.679789349912503], 
'exportfile_SHOENORM': ['1.80E+08_7_0.00098_9.20E-05_0.015_1_0.5', 1.1882999173739865], 
'exportfile_SHOEREVLOOONG2': ['2.20E+08_5_0.00098_9.20E-05_0.015_1_0.5', 2.0755064774562895], 
'exportfile_SHOEREVNORMLOOONG': ['2.20E+08_5_0.00098_9.20E-05_0.015_1_0.5', 1.4599102466531895]}'''


params = {} # {params: {exportfile: 0, ... }, ...}

files = glob.glob('data/hallway/walk/*.csv')
remove = ['data/hallway/walk/exportfile.csv', 'data/hallway/walk/exportfileMAIN.csv', 'data/hallway/walk/exportfiletest.csv']
files = [os.path.basename(x).replace('.csv', '') for x in files if x not in remove]

for thresh in thresholds:
    for win in windows:
        for a in sig_a:
            for w in sig_w:
                for vel in sig_vel:
                    for acc in accs:
                        for gyr in gyrs:
                            # all params gotten
                            results = {}
                            for filename in files:
                                dist = calc_dist(det, win, thresh, trial_type, trial_speed, filename, freq, a, w, vel, acc, gyr)
                                results[filename] = dist
                            p = '_'.join(['%.2E' % Decimal(thresh),str(win),str(a),'%.2E' % Decimal(w),str(vel),str(acc),str(gyr)]) # <-----
                            print (p)
                            params[p] = results

# functionality to use params and gets the best stuff
best_avg_param = [None, -1] # param, best average
best_file_param = dict.fromkeys(files, [None, -1]) # keys: filename, []: param, distance

for param in params:
    vals = params[param].values() # [floats]
    avg = sum(vals) / len(vals)
    if best_avg_param[1] == -1 or best_avg_param[1] > avg:
        best_avg_param = [param, avg]
    for filename in best_file_param:
        if best_file_param[filename][1] == -1 or best_file_param[filename][1] > params[param][filename]:
            best_file_param[filename] = [param, params[param][filename]]

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