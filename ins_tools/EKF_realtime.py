import numpy as np
from numpy import linalg as LA
from ins_tools.util import *
from ins_tools.geometry_helpers import quat2mat, mat2quat, euler2quat, quat2euler
import sys
sys.path.append('../')


import matplotlib.pyplot as plt #################

class Localizer():
    def __init__(self, config, imubatch):
        # config: A dictionary of configuration parameters
        self.config = config

        # Initialise the first batch
        # State vector
        self.x = np.zeros((imubatch.shape[0],9))
        # Quaternion
        self.q = np.zeros((imubatch.shape[0],4))
        # Covariance matrix
        self.P_hat = np.zeros((imubatch.shape[0],9,9))

        avg_x = np.mean(imubatch[0:20,0])
        avg_y = np.mean(imubatch[0:20,1])
        avg_z = np.mean(imubatch[0:20,2]) #gets avg accelerometer values for finding roll/pitch

        heading = 0
        roll = np.arctan2(-avg_y,-avg_z)
        pitch = np.arctan2(avg_x,np.sqrt(avg_y*avg_y + avg_z*avg_z))

        attitude = np.array([roll, pitch, heading])
        # first timestamp 
        self.x[0, 6:9] = attitude # first timestamp 
        self.q[0, :] = euler2quat(roll, pitch, heading, 'sxyz')
        self.P_hat[0,0:3,0:3] = np.power(1e-5,2)*np.identity(3) #position (x,y,z) variance
        self.P_hat[0,3:6,3:6] = np.power(1e-5,2)*np.identity(3) #velocity (x,y,z) variance
        self.P_hat[0,6:9,6:9] = np.power(0.1*np.pi/180,2)*np.identity(3)
    
    def getXQP(self): # return references
        return self.x, self.q, self.P_hat
    
    # Replaces the previous batch with new empty batch with the first value the last value the previous batch
    def nextBatch(self, imushape):
        x = np.zeros((imushape,9))
        q = np.zeros((imushape,4))
        P_hat = np.zeros((imushape,9,9))     
        x[0] = self.x[-1]
        q[0] = self.q[-1]
        P_hat[0] = self.P_hat[-1]
        self.x, self.q, self.P_hat = x, q, P_hat
        return self.x, self.q, self.P_hat
        
    def nav_eq(self,xin,imu,qin,dt):
        '''
        Computes the navigation state update based on IMU measurements using quaternion-based attitude 
        propagation and kinematic equations.

        :param xin: Initial state vector containing positon, velocity and attitude
        :param imu: IMU batch data containing accelerometer and gyroscope data
        :param qin: Initial orientation 
        :param dt: Time step for numerical integration

        :returns: 
            - **x_out** (*ndarray*) – Updated state vector
            - **q_out** (*ndarray*) – Updated quaternion
            - **Rot_out** (*ndarray*) – Rotation matrix corresponding to the updated quaternion
        :rtype: tuple (ndarray, ndarray, ndarray)
        '''
        # Initialise of initial state xin to store updated state 
        x_out = np.copy(xin) 
        # Constructs the skew-symmetric matrix representing angular velocity in quaternion space
        omega = np.array([[0,-imu[3], -imu[4], -imu[5]],  [imu[3], 0, imu[5], -imu[4]],  [imu[4], -imu[5], 0, imu[3]],  [imu[5], imu[4], -imu[3], 0]])

        # Compute norm of angular velocity
        norm_w = LA.norm(imu[3:6])
        if(norm_w*dt != 0): # Quaternion is updated using small-angle rotation formula
            q_out = (np.cos(dt*norm_w/2)*np.identity(4) + (1/(norm_w))*np.sin(dt*norm_w/2)*omega).dot(qin) 
        else: # Quaternion unchanged
            q_out = qin

        # Converts quaternion to euler angles
        attitude = quat2euler(q_out,'sxyz')
        x_out[6:9] = attitude    
        
        # Converts quaternion into rotation matrix
        Rot_out = quat2mat(q_out) 
        # Transform accelerometer data to the navigation frame
        acc_n = Rot_out.dot(imu[0:3])  
        # Adds the gravitational acceleration in the z direction
        acc_n = acc_n + np.array([0,0,self.config["g"]]) 
        
        #Update velocity and position using kinematic equations
        x_out[3:6] += dt*acc_n 
        x_out[0:3] += dt*x_out[3:6] +0.5*np.power(dt,2)*acc_n 
        
        return x_out, q_out, Rot_out    
    
    def state_update(self, imu, q, dt):
        '''
        Computes the state transition matrix (F) and process noise Jacobian matrix (G) for the EKF.

        :param imu: IMU batch data
        :param q: Orientation represented as a quaternion
        :param dt: Time step for numerical integration

        :return: 
            - **F** (*ndarray*) – 9×9 state transition matrix models how errors in state evolve over time,
                    derived by linearizing non linear system dynamics around current state, helps propagate
                    errors in state forward in time
            - **G** (*ndarray*) – 9×6 process noise matrix maps IMU noise to state errors, models how
                    uncertainty from sensor noise affects the system state
        :rtype: tuple (ndarray, ndarray)
        '''
        # State Transition Matrix
        F = np.identity(9)
        F[0:3,3:6] = dt*np.identity(3)
        # Compute rotation matrix and transform accelerometer data
        Rot = quat2mat(q)
        imu_r = Rot.dot(imu[0:3])
        # Constructs the skew-symmetric matrix representing accelerometer data, captures how acceleration
        # affects attitude errors
        f_skew = np.array([[0,-imu_r[2],imu_r[1]],[imu_r[2],0,-imu_r[0]],[-imu_r[1],imu_r[0],0]])
        # Ensures small erros in attitude affects velocity
        F[3:6,6:9] = -dt*f_skew 
        
        # Noise Jacobian Matrix
        G = np.zeros((9,6))
        # Maps accelerometer noise to velocity errors
        G[3:6,0:3] = dt*Rot
        # Maps gyroscope noise to attitude errors
        G[6:9,3:6] = -dt*Rot
       
        return F,G
    
    # Corrects the predicted state using zero-velocity updates (ZUPTs) and the Kalman filter correction step
    def corrector(self, x_check, P_check, Rot):
        '''
        EKF correction step for the predicted states using zero-velocity updates.

        :param x_check: State vector
        :param P_check: Covariance matrix
        :param Rot: Rotation matrix

        :returns: 
            - **x_check** (*ndarray*) – Updated state vector
            - **P_check** (*ndarray*) – Updated covariance matrix
            - **q** (*ndarray*) – Updated quaternion representing the corrected orientation
        :rtype: tuple (ndarray, ndarray, ndarray)
        '''
        # Identity matrices 
        eye3 = np.identity(3) # Attitude correction
        eye9 = np.identity(9) # Covariance updates
        omega = np.zeros((3,3)) # Store skew-symmetric matrix for small roation corrections        
        
        # Uses the measurement model (H) and measurement noise (R) to compute the Kalman gain
        K = (P_check.dot(self.config["H"].T)).dot(LA.inv((self.config["H"].dot(P_check)).dot(self.config["H"].T) + self.config["R"]))
        z = -x_check[3:6] ### true state is 0 velocity, current velocity is error
        q=mat2quat(Rot)   
        # State correction
        dx = K.dot(z) 
        x_check += dx  ###inject position and velocity error
        
        # Constructs the skew-symmetric matrix representing small rotation correction
        omega[0:3,0:3] = [[0,-dx[8], dx[7]],[dx[8],0,-dx[6]],[-dx[7],dx[6],0]] 
        # Rotation matrix updated using correction
        Rot = (eye3+omega).dot(Rot)
        q = mat2quat(Rot)
        attitude = quat2euler(q,'sxyz')
        # Store the updated attitude
        x_check[6:9] = attitude    #Inject rotational error 
        # Covariance update equation to reduce uncertainty based on measurement update        
        P_check = (eye9-K.dot(self.config["H"])).dot(P_check)
        P_check = (P_check + P_check.T)/2
        return x_check, P_check, q

    # Stationary Hypothesis Optimal Estimator (SHOE)
    def SHOE(self, imudata, W=5):
        '''
        Stationary Hypothesis Optimal Estimator (SHOE)
        Analyses IMU data to determine when the system is stationary by computing a test statistic
        based on accelerometer and gyroscope measurements.

        :param imudata: IMU batch data
        :param W: Window size for batch processing

        :returns: Zero-velocity indicator array where lower values indicate stationary periods
        '''
        # Vector storing test statistics for each window
        T = np.zeros(np.int(np.floor(imudata.shape[0]/W)+1))
        # Zero velocity indicator array
        zupt = np.zeros(imudata.shape[0])
        # Temporary arrays for storing accelertion and angular velocity
        a = np.zeros((1,3))
        w = np.zeros((1,3))
        # Inverse of accelerometer and gyroscope noise variance
        inv_a = (1/self.config["var_a"])
        inv_w = (1/self.config["var_w"])
        acc = imudata[:,0:3]
        gyro = imudata[:,3:6]

        # Divides IMU data into non-overlapping windows
        i=0
        for k in range(0,imudata.shape[0]-W+1,W): 
            # Mean acceleration
            smean_a = np.mean(acc[k:k+W,:],axis=0)
            # Loop through each sample in the window and check if stationary
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
        # Test statistic normalised by window size
        zupt = zupt/W
        return zupt
        
    def compute_zv_lrt(self, imudata, W=5, G=3e8, return_zv=True):
        # Compares likelihoods  against a threshold to determine whether zero velocity is detected
        zv = self.SHOE(imudata=imudata, W=W)
        if return_zv:
            zv=zv<G
        return zv

        
