import numpy as np
import matplotlib.pyplot as plt
from ins_tools.INS_realtime import INS
import random

def processData(ins, win, thresh, imubatch, init): 
    zv = ins.Localizer.compute_zv_lrt(imudata=imubatch, W=win, G=thresh)
    x = ins.baseline(imudata=imubatch, zv=zv, init=init)
    return x, zv

thresh = 2.20E+08 
W = 5
sig_a = 0.00098
sig_w = 9.20E-05

imu = np.loadtxt('data/hallway/walk/trial1.csv', delimiter=",", skiprows=1)
print (imu)
ins = None 
batch_pointer = 0
estimates = None
zv = None
init = True

while batch_pointer < len(imu):
    init = ins is None
    if init: # first 20 datapoints, minimum needed by the Localizer
        ins = INS(imu[:20], sigma_a = sig_a, sigma_w = sig_w)
        x, z = processData(ins, W, thresh, imu[:20], init)
        batch_pointer = 20
    else:
        rand = random.randint(5, 20) # substitutes for (length of data collected at the time - batch_pointer)
        batch_size = ((rand // W) * W) - 1 # makes sure it is size 5n - 1
        x, z = processData(ins, W, thresh, imu[batch_pointer-1:batch_pointer+batch_size], init)
        batch_pointer += batch_size
    print(batch_pointer)
    estimates = x if init else np.concatenate((estimates, x[1:]))
    zv = z if init else np.concatenate((zv, z[1:]))

# First plot (Top-down view)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))  
traj_true = estimates[zv] 
axes[0].scatter(-traj_true[:, 0], traj_true[:, 1], color='red', s=30, label='Estimated ZV')
axes[0].plot(-estimates[:, 0], estimates[:, 1], linewidth=1.7, color='blue', label='Trajectory')

axes[0].set_title('Top-down graph', fontsize=16, color='black')
axes[0].set_xlabel('x (m)', fontsize=12)
axes[0].set_ylabel('y (m)', fontsize=12)
axes[0].tick_params(labelsize=12)
axes[0].legend(fontsize=10, numpoints=1)
axes[0].grid()
axes[0].axis('square')

# Second plot (Vertical graph)
num_points = estimates.shape[0]
time_values = np.arange(0, num_points * 1/100, 1/100)[:num_points]
axes[1].plot(time_values, estimates[:, 2], linewidth=1, color='blue', label='Trajectory')

time_zv = time_values[zv]
traj_zv = estimates[zv, 2]
axes[1].scatter(time_zv, traj_zv, color='red', s=30, label='Estimated ZV')

axes[1].set_title('Vertical graph', fontsize=16, color='black')
axes[1].set_xlabel('Time (s)', fontsize=12)
axes[1].set_ylabel('z (m)', fontsize=12)
axes[1].tick_params(labelsize=12)
axes[1].legend(fontsize=10, numpoints=1)
axes[1].grid()

plt.tight_layout()
#plt.savefig('test.png', dpi=400, bbox_inches='tight')
plt.show()

