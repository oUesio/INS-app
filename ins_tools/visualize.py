import matplotlib.pyplot as plt
import numpy as np
import csv

def plot_topdown(traj, title=None, save_dir=None, Loc=4, markerind =[], zv=[], approx=True, estim=True):
    with open('test_zv.csv', mode="r") as f: ####
        reader = csv.reader(f) ####
        next(reader) ####
        data = [int(row) for row in f]  ####

    # Limit the data to the first 3000 points
    #traj = traj[:3000]
    #zv = zv[:3000]

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
        plt.title(title, fontsize=20, color='black')
    plt.xlabel('x (m)', fontsize=22)
    plt.ylabel('y (m)', fontsize=22)
    plt.tick_params(labelsize=22)
    plt.subplots_adjust(top=0.8)
    plt.legend(legend, fontsize=15, numpoints=1)
    # plt.legend(['SHOE'], fontsize=15, numpoints=1) ####
    plt.grid()
    if save_dir:
        plt.savefig(save_dir, dpi=400, bbox_inches='tight')

###Plot the vertical estimate
def plot_vertical(traj, T=1.0/100, title=None, save_dir=None, Loc=4, markerind =[]):
    plt.figure()
    plt.clf()
    num_points = traj.shape[0]
    time_values = np.arange(0, num_points * T, T) 
    plt.plot(time_values, traj[:,2], linewidth = 1, color='blue')
    plt.title(title, fontsize=20, color='black')
    plt.xlabel('Time (s)', fontsize=22)
    plt.ylabel('z (m)', fontsize=22)
    plt.tick_params(labelsize=22)
    plt.legend(['SHOE'], fontsize=15, numpoints=1)
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
