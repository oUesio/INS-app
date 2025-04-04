import numpy as np
from ins_tools.EKF_realtime import Localizer

class INS():
    def __init__(self, imudata, sigma_a=0.01, sigma_w=0.01*np.pi/180, T=1.0/100):
        self.config = {
        "sigma_a": sigma_a,
        "sigma_w": sigma_w,
        "g": 9.8029,
        "T": T,
            }
        # Noise standard deviations
        self.sigma_a = self.config["sigma_a"]
        self.sigma_w = self.config["sigma_w"]
        self.var_a = np.power(self.sigma_a,2)
        self.config["var_a"] = self.var_a
        self.var_w = np.power(self.sigma_w,2)
        self.config["var_w"] = self.var_w

        self.g = self.config["g"]
        self.T = self.config["T"]
        # Variances of the accelerometer and gyroscope noise
        self.sigma_acc = 0.5*np.ones((1,3))
        self.var_acc = np.power(self.sigma_acc,2)
        self.sigma_gyro = 0.5*np.ones((1,3))*np.pi/180
        self.var_gyro = np.power(self.sigma_gyro,2)
        # Combines the variances of accelerometer and gyroscope noises into a covariance matrix
        self.Q = np.zeros((6,6)) 
        self.Q[0:3,0:3] = self.var_acc*np.identity(3)
        self.Q[3:6,3:6] = self.var_gyro*np.identity(3)
        self.config["Q"] = self.Q
        # Measurement noise covariance matrix for velocity measurements
        self.sigma_vel = 0.01 #0.01 default
        self.R = np.zeros((3,3))
        self.R[0:3,0:3] = np.power(self.sigma_vel,2)*np.identity(3)   ##measurement noise, 0.01 default
        self.config["R"] = self.R
        # Measurement matrix mapping state to velocity measurements
        self.H = np.zeros((3,9))
        self.H[0:3,3:6] = np.identity(3)
        self.config["H"]= self.H      

        # Initialises the state vector, quaternion, and state covariance using the Localizer
        self.Localizer = Localizer(self.config, imudata)
        self.x_check, self.q, self.P = self.Localizer.getXQP()
        
    # Performs the core navigation computation
    def baseline(self, imudata, zv, init, G=5e8):
        '''
        Performs the core navigation computation

        :param imudata: IMU batch data
        :param zv: Binary array indicating zero-velocity detection
        :param init: Sets up the state estimates for this batch if false
        :param G: Process noise tuning parameter

        :returns: Estimated position
        '''
        if init is False: # 3 attributes already made when INS initialised
            # Intialises state estimates for this batch
            self.x_check, self.q, self.P = self.Localizer.nextBatch(imudata.shape[0])

        x_hat = self.x_check 
        self.x = x_hat.copy()
        self.zv = zv
        # Skips the first value since Localizer calculated state estimate or the last value of previous batch
        for k in range(1,self.x_check.shape[0]): 
            dt = self.config['T']
            # State prediction, predict next state based on previous step
            self.x_check[k,:], self.q[k,:],Rot = self.Localizer.nav_eq(self.x_check[k-1,:], imudata[k,:], self.q[k-1,:], dt) #update state through motion model
            # Compute state transition matrix (F) and process noise mapping matrix (G)
            F,G = self.Localizer.state_update(imudata[k,:],self.q[k-1,:], dt) 
            # Update the covariance matrix (P) using the prediction model
            self.P[k,:,:] = (F.dot(self.P[k-1,:,:])).dot(F.T) + (G.dot(self.Q)).dot(G.T)
            # Symmetrise the covariance matrix to account for numerical approximations
            self.P[k,:,:] = (self.P[k,:,:] + self.P[k,:,:].T)/2 
            # Corrector step, zero-velocity is detected, the state is corrected using the Kalman update equations
            if self.zv[k] == True: 
                x_hat[k,:], self.P[k,:,:],self.q[k,:] = self.Localizer.corrector(self.x_check[k,:], self.P[k,:,:], Rot )
            else:
                x_hat[k,:] = self.x_check[k,:]
            # Store the state estimate for this time step
            self.x[k,:] = x_hat[k,:]  
        self.x[:,2] = -self.x[:,2] 
        return self.x
    
