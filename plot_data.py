from tools import plot_data


det = 'shoe'

trial_speed = ['run', 'walk', ''][1]
trial_type = ['hallway', 'stairs'][0]
filename = 'stationary'
approx = False ####
estim = True ####
freq = 1/100

thresh = 6e8 #8.5e7 #zero-velocity threshold #1.5e7
win = 5 # 5
sig_a = 0.007 # 0.00098
sig_w = 5.2e-5 # 8.7266463e-5
sig_vel = 0.0007 # 0.01
acc = 0.5 # 0.5
gyr = 0.5 # 0.5

#plot_data(det, win, thresh, trial_type, trial_speed, file_name, freq, approx, estim)  # OLD

'''thresh = 2e8 # 2e8
win = 5 # 5
a = 0.00098 # 0.00098
w = 8.7266463e-5 # 9.2e-5 # 
vel = 0.01 # 0.01
acc = 0.5 # 1 # 
gyr = 0.5 # 0.5'''

plot_data(det, win, thresh, trial_type, trial_speed, filename, freq, sig_a, sig_w, sig_vel, acc, gyr, approx, estim)
