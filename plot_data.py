from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS
import time
import os

from decimal import Decimal

def plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro):# approx, estim):
    start_time = time.time()
    # Gets the imu data from csv file
    with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'), mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro) #microstrain
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    #print (zv.tolist())
    x = ins.baseline(zv=zv)

    if trial_type == 'hallway':
        trial_type += '_'+trial_speed
        if trial_speed == 'comb':
            trial = 'Mixed-Motion Trial'
        if trial_speed == 'run':
            trial = 'Running Trial'
        if trial_speed == 'walk':
            trial = 'Walking Trial'
    if trial_type == 'stairs':
        trial = 'Stair Climbing Trial'
    visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/%s_%s_%s_topdown.png' % (trial_type, file_name, '%.2E' % Decimal(thresh)), zv=zv, approx=approx, estim=estim) ####
    visualize.plot_vertical(x, T=freq, title='{} (Vertical View)'.format(trial), save_dir='results/%s_%s_%s_vert.png' % (trial_type, file_name, '%.2E' % Decimal(thresh)), zv=zv)

    #visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/2test_topdown.png', zv=zv, approx=approx, estim=estim) ####
    #visualize.plot_vertical(x, T=freq, title='{} (Vertical View)'.format(trial), save_dir='results/1test_vert.png', zv=zv)

    print("My program took", time.time() - start_time, "to run")


det = 'shoe'
thresh = 2e8 #8.5e7 #zero-velocity threshold #1.5e7
win = 5   #window size 5

trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
file_name = 'exportfileMAIN'
approx = False ####
estim = True ####
freq = 1/100

temp_sigma_vel=0.01
temp_acc=0.5
temp_gyro=0.5

#plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, temp_sigma_vel, temp_acc, temp_gyro) 

##thresh = 2.2e8 # 2e8
win = 5 # 5
a = 0.00098 # 0.00098
w = 8.7266463e-5 # 9.2e-5 # 
vel = 0.01 # 0.01
acc = 0.5 # 1 # 
gyr = 0.5 # 0.5

#plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, vel, acc, gyr)
