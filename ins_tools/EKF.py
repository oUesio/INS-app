import numpy as np
from numpy import linalg as LA
from ins_tools.util import *
from ins_tools.geometry_helpers import quat2mat, mat2quat, euler2quat, quat2euler
import sys
sys.path.append('../')


import matplotlib.pyplot as plt #################

class Localizer():
    def __init__(self, config, imudata):
        # config: A dictionary of configuration parameters
        self.config = config
        self.imudata = imudata
    def init(self):
        imudata = self.imudata 
        # Initialise state to be at 0
        x = np.zeros((imudata.shape[0],9))
        # #Initialise quaternion 
        q = np.zeros((imudata.shape[0],4))
        avg_x = np.mean(imudata[0:20,0])
        avg_y = np.mean(imudata[0:20,1])
        avg_z = np.mean(imudata[0:20,2]) #gets avg accelerometer values for finding roll/pitch
        
        heading = 0
        roll = np.arctan2(-avg_y,-avg_z)
        pitch = np.arctan2(avg_x,np.sqrt(avg_y*avg_y + avg_z*avg_z))
           
        attitude = np.array([roll, pitch, heading])
        x[0, 6:9] = attitude
        q[0, :] = euler2quat(roll, pitch, heading, 'sxyz')

        # Initialise covariance matrix P
        P_hat = np.zeros((imudata.shape[0],9,9))
        P_hat[0,0:3,0:3] = np.power(1e-5,2)*np.identity(3) #position (x,y,z) variance
        P_hat[0,3:6,3:6] = np.power(1e-5,2)*np.identity(3) #velocity (x,y,z) variance
        P_hat[0,6:9,6:9] = np.power(0.1*np.pi/180,2)*np.identity(3) #np.power(0.1*np.pi/180,2)*np.identity(3)
        return x, q, P_hat
    
    # Updates the state vector based on the motion model
    def nav_eq(self,xin,imu,qin,dt):
        #update Quaternions
        x_out = np.copy(xin) #initialize the output
        omega = np.array([[0,-imu[3], -imu[4], -imu[5]],  [imu[3], 0, imu[5], -imu[4]],  [imu[4], -imu[5], 0, imu[3]],  [imu[5], imu[4], -imu[3], 0]])

        # Use gyroscope data to update the quaternion, apply angular velocity using Rodrigues’ rotation formula.
        norm_w = LA.norm(imu[3:6])
        if(norm_w*dt != 0):
            q_out = (np.cos(dt*norm_w/2)*np.identity(4) + (1/(norm_w))*np.sin(dt*norm_w/2)*omega).dot(qin) 
        else:
            q_out = qin

        attitude = quat2euler(q_out,'sxyz')#update euler angles
        x_out[6:9] = attitude    
        
        Rot_out = quat2mat(q_out)   #get rotation matrix from quat
        acc_n = Rot_out.dot(imu[0:3])       #transform acc to navigation frame,  
        acc_n = acc_n + np.array([0,0,self.config["g"]])   #removing gravity (by adding)
        
        #Update velocity  and position using kinematic equations
        x_out[3:6] += dt*acc_n #velocity update
        x_out[0:3] += dt*x_out[3:6] +0.5*np.power(dt,2)*acc_n #position update
        
        # Updated state vector, Updated quaternion, Rotation matrix .
        return x_out, q_out, Rot_out    
    
    # Computes the state transition (F) and noise Jacobian (G) matrices for the EKF
    def state_update(self, imu,q, dt):
        # State Transition Matrix, Models the relationship between states (position, velocity, orientation) over time
        # Accounts for linear velocity update and the effect of rotation on acceleration
        F = np.identity(9)
        F[0:3,3:6] = dt*np.identity(3)

        Rot = quat2mat(q)
        imu_r = Rot.dot(imu[0:3])
        f_skew = np.array([[0,-imu_r[2],imu_r[1]],[imu_r[2],0,-imu_r[0]],[-imu_r[1],imu_r[0],0]])
        F[3:6,6:9] = -dt*f_skew 
        
        # Noise Jacobian Matrix, Maps process noise (accelerometer and gyroscope noise) into the state space
        # Includes contributions of rotation matrix
        G = np.zeros((9,6))
        G[3:6,0:3] = dt*Rot
        G[6:9,3:6] = -dt*Rot
       
        return F,G
    
    # Corrects the predicted state using zero-velocity updates (ZUPTs) and the Kalman filter correction step
    def corrector(self, x_check, P_check, Rot):
        eye3 = np.identity(3)
        eye9 = np.identity(9)
        omega = np.zeros((3,3))        
        
        # Uses the measurement model (H matrix) and measurement noise (R) to compute the Kalman gain
        K = (P_check.dot(self.config["H"].T)).dot(LA.inv((self.config["H"].dot(P_check)).dot(self.config["H"].T) + self.config["R"]))
        z = -x_check[3:6] ### true state is 0 velocity, current velocity is error
        q=mat2quat(Rot)   
        dx = K.dot(z) 
        x_check += dx  ###inject position and velocity error
         
        omega[0:3,0:3] = [[0,-dx[8], dx[7]],[dx[8],0,-dx[6]],[-dx[7],dx[6],0]] 
        Rot = (eye3+omega).dot(Rot)
        q = mat2quat(Rot)
        attitude = quat2euler(q,'sxyz')
        x_check[6:9] = attitude    #Inject rotational error 
        # Apply the Kalman filter correction step to update the covariance matrix          
        P_check = (eye9-K.dot(self.config["H"])).dot(P_check)
        P_check = (P_check + P_check.T)/2
        # Corrected state vector (x_check), covariance matrix (P_check), and quaternion (q)
        return x_check, P_check, q

    # Stationary Hypothesis Optimal Estimator (SHOE)
    def SHOE(self, W=5):
        imudata = self.imudata
        # Divide the IMU data into windows, Compute test statistics for each window
        T = np.zeros(np.int(np.floor(imudata.shape[0]/W)+1))
        zupt = np.zeros(imudata.shape[0])
        a = np.zeros((1,3))
        w = np.zeros((1,3))
        # Compute inverse of noise variances
        inv_a = (1/self.config["var_a"])
        inv_w = (1/self.config["var_w"])
        # First 3 is accelerometer data
        acc = imudata[:,0:3]
        # Next 3 is angular velocity
        gyro = imudata[:,3:6]
    
        i=0
        for k in range(0,imudata.shape[0]-W+1,W): #filter through all imu readings
            # Compute mean acceleration for window
            smean_a = np.mean(acc[k:k+W,:],axis=0)
            # Loop through each time step in the window
            for s in range(k,k+W):
                # Update acceleration and angular velocity
                a.put([0,1,2],acc[s,:])
                w.put([0,1,2],gyro[s,:])
                # Add contribution of acceleration to test statistic
                T[i] += inv_a*( (a - self.config["g"]*smean_a/LA.norm(smean_a)).dot(( a - self.config["g"]*smean_a/LA.norm(smean_a)).T)) #acc terms
                # Add contribution of angular velocity to the test statistic
                T[i] += inv_w*( (w).dot(w.T) )
            zupt[k:k+W].fill(T[i])
            i+=1
        zupt = zupt/W
        # Zero-velocity likelihood
        return zupt
        
    ### if a custom zero-velocity detector was added as a function above, additionally modify this list:    
    def compute_zv_lrt(self, W=5, G=3e8, return_zv=True): #import window size, zv-threshold
        # Compares likelihoods  against a threshold to determine whether zero velocity is detected
        zv = self.SHOE(W=W)
        #################
        data = np.array(zv[0:2500])
        plt.figure(figsize=(13, 5))
        plt.plot(range(len(data)), data, linestyle='-', color='b')
        plt.axhline(y=G, color='r', linestyle='--')

        # Labels and title
        plt.xlabel('Index')
        plt.ylabel('ZV')
        plt.title('ZV before threshold')
        plt.grid(True)    
        plt.savefig("test_zv/test_zv.png")
        #################
        if return_zv:
            zv=zv<G
        return zv

        
