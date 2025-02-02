from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS
import time
import os

from decimal import Decimal


start_time = time.time()

det = 'shoe'
thresh = 8.5e7#1e7 #zero-velocity threshold
win = 5   #window size

trial_speed = ['run', 'walk', ''][0]
trial_type = ['hallway', 'stairs'][0]
file_name = 'exportfile'
approx = False ####
estim = True ####
freq = 1/100


# Gets the imu data from csv file
with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'), mode="r") as file:
    reader = csv.reader(file)
    next(reader)
    imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

print ('1. Initialise INS object (would have entire data already)')
ins = INS(imu, sigma_a = 0.00098, sigma_w = 8.7266463e-5, T=freq) #microstrain

###Estimate trajectory for shoe zv detector
zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
#print (zv.tolist())

print ('10. baseline using zupt')
x = ins.baseline(zv=zv)

print ('15. Plot')
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
visualize.plot_vertical(x, T=freq, title='{} (Vertical View)'.format(trial), save_dir='results/%s_%s_%s_vert.png' % (trial_type, file_name, '%.2E' % Decimal(thresh)))
# add plot_vel and plot acc?
print("My program took", time.time() - start_time, "to run")
