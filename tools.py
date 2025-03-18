import numpy as np
import csv
import time
import os 
from ins_tools.util import *
from ins_tools.INS import INS
import ins_tools.visualize as visualize
from decimal import Decimal
import matplotlib.pyplot as plt


'''def export_csv(csv_name, data):
    with open(csv_name+'.csv', "w") as outfile:
        dict_writer = csv.DictWriter(outfile, data[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(data)'''

def read_imu_csv(csv_file):
    with open(csv_file, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        imu = np.array([list(map(float, row)) for row in reader], dtype=float) 
        return imu

def plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro, approx, estim):# approx, estim):
    start_time = time.time()
    imu = read_imu_csv(os.path.join('data',trial_type,trial_speed,file_name+'.csv'))

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro) #microstrain
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh)
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
    visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/%s_%s_%s_topdown.png' % (trial_type, file_name, '%.2E' % Decimal(thresh)), zv=zv) ####
    visualize.plot_vertical(x, T=freq, title='{} (Vertical View)'.format(trial), save_dir='results/%s_%s_%s_vert.png' % (trial_type, file_name, '%.2E' % Decimal(thresh)), zv=zv)
    visualize.plot_acc(x,'results/temp_acc.png')
    visualize.plot_vel(x,'results/temp_vel.png')
    #visualize.plot_topdown(x, title='{} (Top-Down View)'.format(trial), save_dir='results/2test_topdown.png', zv=zv, approx=approx, estim=estim) ####
    #visualize.plot_vertical(x, T=freq, title='{} (Vertical View)'.format(trial), save_dir='results/1test_vert.png', zv=zv)

    print("My program took", time.time() - start_time, "to run")

def plot_data_temp(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro, approx, estim):# approx, estim):
    imu = read_imu_csv(os.path.join('data',trial_type,trial_speed,file_name+'.csv'))

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro) #microstrain
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    x = ins.baseline(zv=zv)

    visualize.plot_topdown(x, title='{}'.format(file_name.replace('exportfile', '').replace('_', '')), save_dir='results/%s' % (file_name.replace('exportfile', '').replace('_', '')), zv=zv) 
    visualize.plot_vertical(x, title='{}'.format(file_name.replace('exportfile', '').replace('_', '')), save_dir='results_vert/%s' % (file_name.replace('exportfile', '').replace('_', '')), zv=zv) 

def calc_dist(det, win, thresh, trial_type, trial_speed, file_name, freq, a, w, temp_sigma_vel, temp_acc, temp_gyro):
    imu = read_imu_csv(os.path.join('data',trial_type,trial_speed,file_name+'.csv'))

    # sigma_a = 0.00098, sigma_w = 8.7266463e-5
    ins = INS(imu, sigma_a = a, sigma_w = w, T=freq, temp_sigma_vel=temp_sigma_vel, temp_acc=temp_acc, temp_gyro=temp_gyro)
    zv = ins.Localizer.compute_zv_lrt(W=win, G=thresh, detector=det)
    x = ins.baseline(zv=zv)

    #print (x[-1, :3])
    #return np.linalg.norm(x[-1,:3]) # distance between final point and 3D
    return np.linalg.norm(x[-1,:2]) # 2d

def save_topdown(traj, zv, save_dir=None):
    # Make the same size
    min_len = min(len(traj), len(zv))
    traj = traj[:min_len]
    zv = zv[:min_len]
    plt.figure()

    traj_true = traj[zv]  # Select points where zv is True
    plt.scatter(-traj_true[:, 0], traj_true[:, 1], color='red', s=30, label='Estimated ZV')

    plt.plot(-traj[:,0], traj[:,1], linewidth = 1.7, color='blue', label='Trajectory')
    plt.title('Topdown graph', fontsize=16, color='black')
    plt.xlabel('x (m)', fontsize=12)
    plt.ylabel('y (m)', fontsize=12)
    plt.tick_params(labelsize=12)
    plt.subplots_adjust(top=0.8)
    plt.legend(fontsize=10, numpoints=1)
    plt.grid()
    plt.axis('square') 
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')