from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS
import glob
import time
import os

start_time = time.time()

source_dir = "data/hallway/"
stats = []
saved_trajectories = {}

        ###add custom detector and its zv output to lists:
det = 'shoe'
thresh =  8.5e7 #zero-velocity thresholds for various detectors (lstm has no threshold)
win = 5   #window size used for classical detectors (LSTM requires no window size)
legend = ['SHOE'] #used for plotting results.

#for f in sorted(glob.glob('{}*/*.csv'.format(source_dir))):
file_name = 'test_data'

for f in glob.glob('%s*/%s.csv' % (source_dir, file_name)):
    # Gets the imu data from csv file
    with open(f, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        imu = np.array([list(map(float, row)) for row in reader], dtype=float) 

    trial_type = os.path.relpath(f, source_dir).rsplit(f'/{file_name}.csv', 1)[0]
    print ('1. Initialise INS object (would have entire data already)')
    ins = INS(imu, sigma_a = 0.00098, sigma_w = 8.7266463e-5, T=1.0/200) #microstrain
    '''
    imudata: IMU data (likely an array of measurements).
    sigma_a: Standard deviation of accelerometer noise.
    sigma_w: Standard deviation of gyroscope noise (converted to radians).
    T: Default sampling period (1/125 Hz).
    dt: Optional time intervals between measurements (if non-uniform sampling).
    '''

    ###Estimate trajectory for shoe zv detector
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    print ('10. baseline using zupt')
    x = ins.baseline(zv=zv)

    if trial_type == 'comb':
        trial = 'Mixed-Motion Trial'
    if trial_type == 'run':
        trial = 'Running Trial'
    if trial_type == 'walk':
        trial = 'Walking Trial'
    print ('15. Plot')
    visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/%s_%s.png' % (trial_type, file_name), legend=legend)
    print("My program took", time.time() - start_time, "to run")
