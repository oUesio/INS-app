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
legend = ['SHOE'] #used for plotting results

trial_speed = ['run', 'walk'][1]
file_name = 'exportfile'
approx = False ####
estim = True ####


# Gets the imu data from csv file
with open(os.path.join('data','hallway',trial_speed,file_name+'.csv'), mode="r") as file:
    reader = csv.reader(file)
    next(reader)
    imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

print ('1. Initialise INS object (would have entire data already)')
ins = INS(imu, sigma_a = 0.00098, sigma_w = 8.7266463e-5, T=1.0/100) #microstrain

###Estimate trajectory for shoe zv detector
zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
#print (zv.tolist())

print ('10. baseline using zupt')
x = ins.baseline(zv=zv)

if trial_speed == 'comb':
    trial = 'Mixed-Motion Trial'
if trial_speed == 'run':
    trial = 'Running Trial'
if trial_speed == 'walk':
    trial = 'Walking Trial'

print ('15. Plot')
visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/%s_%s_%s_%s.png' % ('hallway', trial_speed, file_name, '%.2E' % Decimal(thresh)), legend=legend, zv=zv, approx=approx, estim=estim) ####
print("My program took", time.time() - start_time, "to run")
