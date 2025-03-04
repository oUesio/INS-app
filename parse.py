from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS
import time
import os
import sys

from decimal import Decimal

class Parse:
    def __init__(self):
        self.running = False

    def getRunning(self):
        return self.running
    
    def toggleRunning(self):
        self.running = not self.running

    def plot_data(self, trial_type, trial_speed, file_name):
        self.toggleRunning()
        if not trial_type:
            trial_type = "hallway"
        if not trial_speed:
            trial_speed = "walk"
        if not file_name:
            file_name = "exportfile"
        
        start_time = time.time()

        det = 'shoe'
        thresh = 8.5e7 #zero-velocity threshold
        win = 5   #window size
        legend = ['SHOE'] #used for plotting results

        try:
            with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'), mode="r") as file:
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

            visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/%s_%s_%s_%s.png' % ('hallway', trial_speed, file_name, '%.2E' % Decimal(thresh)), legend=legend, zv=zv)
            print("My program took", time.time() - start_time, "to run")
            self.toggleRunning()
        except FileNotFoundError:
            self.toggleRunning()
            print(f"Error: File '{os.path.join('data',trial_type,trial_speed,file_name+'.csv')}' not found.")
            sys.exit(1)
        except Exception as e:
            self.toggleRunning()
            print(f"Unexpected error: {e}")
            sys.exit(1)