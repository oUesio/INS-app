import numpy as np
from ins_tools.util import *
from ins_tools.EKF import Localizer

class INS():
    def __init__(self, imudata, sigma_a=0.01, sigma_w=0.01*np.pi/180, T=1.0/100, temp_sigma_vel=0.01, temp_acc=0.5, temp_gyro=0.5):
        self.config = {
        "sigma_a": sigma_a,
        "sigma_w": sigma_w,
        "g": 9.8029,
        "T": T,
            }
        # Stores the input IMU data
        self.imudata = imudata
        # Noise standard deviations
        self.sigma_a = self.config["sigma_a"]
        self.sigma_w = self.config["sigma_w"]
        self.var_a = np.power(self.sigma_a,2)
        self.config["var_a"] = self.var_a
        self.var_w = np.power(self.sigma_w,2)
        self.config["var_w"] = self.var_w

        self.g = self.config["g"]
        self.T = self.config["T"]
        ##process noise in body frame
        # Variances of the accelerometer and gyroscope noise
        self.sigma_acc = temp_acc*np.ones((1,3))
        self.var_acc = np.power(self.sigma_acc,2)
        self.sigma_gyro = temp_gyro*np.ones((1,3))*np.pi/180
        self.var_gyro = np.power(self.sigma_gyro,2)
        ##process noise covariance matrix Q
        # Combines the variances of accelerometer and gyroscope noises into a covariance matrix
        self.Q = np.zeros((6,6)) 
        self.Q[0:3,0:3] = self.var_acc*np.identity(3)
        self.Q[3:6,3:6] = self.var_gyro*np.identity(3)
        self.config["Q"] = self.Q
        # Measurement noise covariance matrix for velocity measurements
        # Assumes a small noise level (0.01)
        self.sigma_vel = temp_sigma_vel #0.01 default
        self.R = np.zeros((3,3))
        self.R[0:3,0:3] = np.power(self.sigma_vel,2)*np.identity(3)   ##measurement noise, 0.01 default
        self.config["R"] = self.R
        # Measurement matrix mapping state to velocity measurements
        self.H = np.zeros((3,9))
        self.H[0:3,3:6] = np.identity(3)
        self.config["H"]= self.H        
        # Localizer instance for EKF updates
        self.Localizer = Localizer(self.config, imudata)
        
    # Performs the core navigation computation
    def baseline(self,W=5, G=5e8, detector='shoe', zv=None):
        imudata = self.imudata
        
        # Initialises the state vector, quaternion, and state covariance using the Localizer
        x_check,q, P = self.Localizer.init() #initialize state
        x_hat = x_check 
        self.x = x_hat
        
        if zv is None:
            ### Compute the trial's zero-velocity detections using the specified detector
            self.zv = self.Localizer.compute_zv_lrt(W,G, detector=detector) #ZV detection 
        else:
            ### Use a pre-computed zero-velocity estimate
            self.zv = zv
        for k in range(1,x_check.shape[0]):      
            dt = self.config['T']
            # State prediction, predict next state based on previous step
            x_check[k,:], q[k,:],Rot = self.Localizer.nav_eq(x_check[k-1,:], imudata[k,:], q[k-1,:], dt) #update state through motion model
            # Compute state transition matrix (F) and process noise mapping matrix (G)
            F,G = self.Localizer.state_update(imudata[k,:],q[k-1,:], dt) 
            # Update the covariance matrix (P) using the prediction model
            P[k,:,:] = (F.dot(P[k-1,:,:])).dot(F.T) + (G.dot(self.Q)).dot(G.T)
            # Symmetrize the covariance matrix to account for numerical approximations
            P[k,:,:] = (P[k,:,:] + P[k,:,:].T)/2 #make symmetric
            # Corrector step, zero-velocity is detected, the state is corrected using the Kalman update equations
            if self.zv[k] == True: 
                x_hat[k,:], P[k,:,:], q[k,:] = self.Localizer.corrector(x_check[k,:], P[k,:,:], Rot )
            else:
                x_hat[k,:] = x_check[k,:]
            # Store the updated state estimate for this time step
            self.x[k,:] = x_hat[k,:]  
        self.x[:,2] = -self.x[:,2] 
        self.rot = self.x[:,6:9]
        self.q = q
        self.P = P
        # Return the complete state estimates for all time steps
        '''
        print (self.q)

        header = ['q0', 'q1', 'q2', 'q3']
        with open('calculated_quaternion.csv', "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(self.q)
        '''
        return self.x
    
