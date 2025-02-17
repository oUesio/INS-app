import matplotlib.pyplot as plt
import numpy as np
import csv

def plot_topdown(traj, title=None, save_dir=None, zv=[], approx=True, estim=True):
    with open('test_zv.csv', mode="r") as f: ####
        reader = csv.reader(f) ####
        next(reader) ####
        data = [int(row) for row in f]  ####

    #traj = traj[:2500]
    #zv = zv[:2500]

    plt.figure()
    plt.clf()
    plt.plot(-traj[:,0], traj[:,1], linewidth = 1.7, color='blue')

    legend = ['SHOE'] ####
    if estim:
        if len(zv) != 0:
            traj_true = traj[zv]  # Select points where zv is True
            plt.scatter(-traj_true[:, 0], traj_true[:, 1], color='red', s=30)
            legend.append('Estimated ZV')

    if approx: ####
        if len(data) > 0: ####
            traj_data = traj[data]  # Select points using indexes from CSV ####
            plt.scatter(-traj_data[:, 0], traj_data[:, 1], facecolors='none', color='green', s=30) ####
            legend.append('Approx actual ZV') ####

    if title != None:
        plt.title(title, fontsize=16, color='black')
    plt.xlabel('x (m)', fontsize=12)
    plt.ylabel('y (m)', fontsize=12)
    plt.tick_params(labelsize=12)
    plt.subplots_adjust(top=0.8)
    plt.legend(legend, fontsize=10, numpoints=1)
    # plt.legend(['SHOE'], fontsize=15, numpoints=1) ####
    plt.grid()
    plt.axis('square') 
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')

###Plot the vertical estimate
def plot_vertical(traj, T=1.0/100, title=None, save_dir=None, zv=[]):
    #traj = traj[:4000]
    #zv = zv[:4000]

    plt.figure()
    plt.clf()
    num_points = traj.shape[0]
    try:
        time_values = np.arange(0, num_points * T, T)[:-1] 
        plt.plot(time_values, traj[:,2], linewidth = 1, color='blue')
    except:
        time_values = np.arange(0, num_points * T, T)
        plt.plot(time_values, traj[:,2], linewidth = 1, color='blue')
 
    legend = ['SHOE'] ####
    if len(zv) != 0:
        time_zv = time_values[zv]
        traj_zv = traj[zv, 2]
        #traj_true = traj[zv]  # Select points where zv is True
        plt.scatter(time_zv, traj_zv, color='red', s=30)
        legend.append('Estimated ZV')

    if title != None:
        plt.title(title, fontsize=16, color='black')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('z (m)', fontsize=12)
    plt.tick_params(labelsize=12)
    plt.subplots_adjust(top=0.8)
    plt.legend(legend, fontsize=10, numpoints=1)
    plt.grid()
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')       

###plot IMU linear acceleration
def plot_acc(imudata, save_dir):
    plt.figure()
    plt.tick_params(labelsize=19)
    plt.plot(imudata[:,0]/9.8)
    plt.plot(imudata[:,1]/9.8)
    plt.plot(imudata[:,2]/9.8)
    plt.title(['Linear Acceleration'], fontsize=19)
    plt.legend(['x', 'y', 'z'], fontsize=14)
    plt.ylabel('linear acceleration (Gs)', fontsize=19)
    plt.grid()
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')

###plot IMU angular velocity
def plot_vel(imudata, save_dir):
    plt.figure()
    plt.tick_params(labelsize=19)
    plt.plot(imudata[:,3]*180/np.pi)
    plt.plot(imudata[:,4]*180/np.pi)
    plt.plot(imudata[:,5]*180/np.pi)
    plt.title(['Angular Velocity'],fontsize=19)
    plt.legend(['x', 'y', 'z'], fontsize=14)
    plt.ylabel('Angular Velocity (deg/s)', fontsize=19)
    plt.grid()
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')
