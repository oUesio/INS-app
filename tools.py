import numpy as np
import matplotlib.pyplot as plt

def save_topdown(traj, zv, name, speed, save_dir):
    # Make the same size
    min_len = min(len(traj), len(zv))
    traj = traj[:min_len]
    zv = zv[:min_len]
    plt.figure()

    traj_true = traj[zv]  # Select points where zv is True
    plt.scatter(-traj_true[:, 0], traj_true[:, 1], color='red', s=30, label='Estimated ZV')

    plt.plot(-traj[:,0], traj[:,1], linewidth = 1.7, color='blue', label='Trajectory')
    plt.title(f'Topdown graph: {speed} {name}', fontsize=16, color='black')
    plt.xlabel('x (m)', fontsize=12)
    plt.ylabel('y (m)', fontsize=12)
    plt.tick_params(labelsize=12)
    plt.subplots_adjust(top=0.8)
    plt.legend(fontsize=10, numpoints=1)
    plt.grid()
    plt.axis('square') 
    plt.savefig(save_dir, dpi=400, bbox_inches='tight')

def save_vertical(traj, zv, name, speed, save_dir, T=1.0/100):
    min_len = min(len(traj), len(zv))
    traj = traj[:min_len]
    zv = zv[:min_len]
    plt.figure()

    num_points = traj.shape[0]
    time_values = np.arange(0, num_points * T, T)[:num_points]
    plt.plot(time_values, traj[:,2], linewidth = 1, color='blue', label='Trajectory')
 
    time_zv = time_values[zv]
    traj_zv = traj[zv, 2]
    plt.scatter(time_zv, traj_zv, color='red', s=30, label='Estimated ZV')

    plt.title(f'Vertical graph: {speed} {name}', fontsize=16, color='black')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('z (m)', fontsize=12)
    plt.tick_params(labelsize=12)
    plt.subplots_adjust(top=0.8)
    plt.legend(fontsize=10, numpoints=1)
    plt.grid()
    plt.savefig(save_dir, dpi=400, bbox_inches='tight')       
