import numpy as np
import os
from ins_tools.INS_realtime import INS
import math

def calc_dist(x):
    return np.linalg.norm(x) # 2d

estimates = 'results/estimates'

# Distances travelled for the different conditions
dists = {'walk':42.8, 'run':42.8, 'mixed':42.8, '1F':9.1, '2F':24.95, '3F':40.8}
total = {'walk':[], 'run':[], 'mixed':[], '1F':[], '2F':[], '3F':[]}
# Real-time estimates
for filename in sorted(os.listdir(estimates)):
    if ("walk_trial" in filename or "run_trial" in filename or "mixed_trial" in filename) and filename.endswith(".csv"): 
        file_path = os.path.join(estimates, filename)
        data = np.loadtxt(file_path, delimiter=",", skiprows=1)
        
        # XY Plane
        last_values = data[-1, :2]
        if "walk_trial" in filename:
            total['walk'].append(calc_dist(last_values))
        elif "run_trial" in filename:
            total['run'].append(calc_dist(last_values))
        else:
            total['mixed'].append(calc_dist(last_values))
        
        #print(f"File: {filename}, XY distance: {calc_dist(last_values)}")

    if ("stairs_trial" in filename) and filename.endswith(".csv"):
        file_path = os.path.join(estimates, filename)
        data = np.loadtxt(file_path, delimiter=",", skiprows=1)
        
        # XYZ Space
        last_values = data[-1, :3]
        if "1F" in filename:
            total['1F'].append(calc_dist(last_values))
        elif "2F" in filename:
            total['2F'].append(calc_dist(last_values))
        else:
            total['3F'].append(calc_dist(last_values))
        
        #print(f"File: {filename}, XYZ distance: {calc_dist(last_values)}")

print (total)
for x in total:
    mean = sum(total[x]) / 9
    # Average loop closure error
    print (x + ' position error: ' + str(round(mean,4)) + 'm')
    # Average relative error
    print (x + ' relative error: ' + str(round((mean/dists[x])*100, 4)) + '%')
    # Standard deviation
    print (x + ' sd: ' + str(round(math.sqrt(sum((val - mean) ** 2 for val in total[x]) / (len(total[x]) - 1)),4)))

def full_estimates(trial_type, trial_speed, file_name):
    """
    Loads IMU data from a raw IMU data CSV file and initialises the INS to process the data all at once.

    :param trial_type: Type of trial (hallway or stairs)
    :param trial_speed: Movement speed (walk, run, or mixed)
    :param file_name: IMU data file name

    :returns: 
        - **x** (*ndarray*) – Array of estimated states from the INS
    :rtype: ndarray
    """
    imu = np.loadtxt(os.path.join('data',trial_type,trial_speed,file_name), delimiter=",", skiprows=1)
    ins = INS(imu, sigma_a = 0.00098, sigma_w = 9.20E-05)
    zv = ins.Localizer.compute_zv_lrt(imu, W=5, G=2.20E+08)
    x = ins.baseline(imudata=imu, zv=zv, init=True)

    return x

total_full = {'walk':[], 'run':[], 'mixed':[], '1F':[], '2F':[], '3F':[]}
dirs = ['walk', 'run', 'mixed', 'stairs']
for d in dirs:
    if d == 'stairs':
        full = 'data/'+d
        for filename in sorted(os.listdir(full)):
            if ('trial' in filename) and filename.endswith(".csv"): 
                if "1F" in filename:
                    total_full['1F'].append(calc_dist(full_estimates('stairs', '', filename)[-1,:3]))
                elif "2F" in filename:
                    total_full['2F'].append(calc_dist(full_estimates('stairs', '', filename)[-1,:3]))
                else:
                    total_full['3F'].append(calc_dist(full_estimates('stairs', '', filename)[-1,:3]))
    else:
        full = 'data/hallway/'+d
        for filename in sorted(os.listdir(full)):
            if ('trial' in filename) and filename.endswith(".csv"): 
                total_full[d].append(calc_dist(full_estimates('hallway', d, filename)[-1,:2]))

print (total_full)
for x in total_full:
    mean = sum(total_full[x]) / 9
    print (x + ' full position error: ' + str(round(mean,4)) + 'm')
    print (x + ' full relative error: ' + str(round((mean/dists[x])*100, 4)) + '%')
    print (x + ' sd: ' + str(round(math.sqrt(sum((val - mean) ** 2 for val in total[x]) / (len(total[x]) - 1)),4)))

