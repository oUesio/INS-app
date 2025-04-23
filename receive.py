import sys
import numpy as np
import xsensdeviceapi as xda
from threading import Lock
import os
from ins_tools.INS_realtime import INS
import tools

class XdaCallback(xda.XsCallback):
    """
    Custom callback handler for handling live IMU data from the Xsens device.

    :ivar m_lock: Thread lock to ensure thread-safe access to the data list
    :ivar data_list: Accumulated list of IMU data (acceleration and gyroscope)
    """
    def __init__(self):
        xda.XsCallback.__init__(self)
        self.m_lock = Lock() # Thread lock
        self.data_list = [] 

    def onLiveDataAvailable(self, dev, packet):
        """
        Callback function triggered when new data is available.

        :param dev: Device pointer (not used)
        :param packet: IMU data packet containing acceleration and gyroscope data
        """
        self.m_lock.acquire()
        assert(packet != 0) # Ensure the packet is valid
        acc = packet.calibratedAcceleration()
        gyr = packet.calibratedGyroscopeData()
        
        data = list(acc)+list(gyr)
        self.data_list.append(data) 

        self.m_lock.release()

    def getLengthData(self):
        """Returns the length of the collected data list."""
        return len(self.data_list)

    def getData(self):
        """Returns the collected IMU data."""
        return self.data_list

class Receive:
    """
    Manages data collection from the Xsens device and processes it using the INS algorithm.

    :ivar callback: Instance of XdaCallback for handling live IMU data
    :ivar ins: Instance of the INS model used for trajectory estimation
    :ivar estimates: Array of estimated states from the INS
    :ivar zv: Zero velocity detection flags
    """
    def __init__(self):
        self.stop = False
        self.running = False
        self.callback = XdaCallback() 
        self.ins = None
        self.estimates = None
        self.zv = None

    def getStop(self):
        """Returns the current stop state."""
        return self.stop
    
    def getRunning(self):
        """Returns the current running state."""
        return self.running

    def setStop(self, state):
        """Sets the stop state."""
        self.stop = state

    def setRunning(self, state):
        """Sets the running state."""
        self.running = state

    def getRawData(self):
        """Returns the raw IMU data collected."""
        return self.callback.getData()
    
    def getEstimates(self):
        """
        Returns the current INS estimates and zero velocity detections.
        """
        return self.estimates, self.zv
    
    def processData(self, imubatch, W, threshold, init):
        """
        Processes a micro-batch of IMU data using zero-velocity detection and INS baseline estimation.

        :param imubatch: Array of IMU micro-batch data
        :param W: Window size used in the  zero-velocity detector
        :param threshold: Threshold value for the zero-velocity detector
        :param init: Boolean flag to indicate if it is the initial estimation step
        """
        zv = self.ins.Localizer.compute_zv_lrt(imudata=imubatch, W=W, G=threshold)
        estimates = self.ins.baseline(imudata=imubatch, zv=zv, init=init)

        self.estimates = estimates if init else np.concatenate((self.estimates, estimates[1:]))
        self.zv = zv if init else np.concatenate((self.zv, zv[1:]))

    def main(self, trial_type, trial_speed, file_name):
        """
        Main method to run the data collection, processing, and saving.

        :param trial_type: Type of trial (hallway or stairs)
        :param trial_speed: Movement speed (walk, run, or mixed)
        :param file_name: Output file name
        """
        self.callback = XdaCallback() # Resets callback
        self.ins = None # resets ins
        # Default values
        if not trial_type:
            trial_type = "hallway"
        if not trial_speed:
            trial_speed = "walk"
        if not file_name:
            file_name = "exportfile"
        if trial_type not in ['hallway', 'stairs']:
            raise RuntimeError("Invalid trial type (hallway, stairs). Aborting.")
        if trial_type == 'hallway' and trial_speed not in ['walk', 'run', 'mixed']:
            raise RuntimeError("Invalid trial speed for hallway (walk, run, mixed). Aborting.")

        # Create XsControl object
        control = xda.XsControl_construct()
        assert(control != 0)

        xda_version = xda.XsVersion()
        xda.xdaVersion(xda_version)
        print("Using XDA version %s" % xda_version.toXsString())

        try:
            # Scan for connected Xsens devices
            port_info_array =  xda.XsScanner_scanPorts() 
            # Find an MTi device
            mt_port = xda.XsPortInfo()
            for i in range(port_info_array.size()):
                if port_info_array[i].deviceId().isMti() or port_info_array[i].deviceId().isMtig():
                    mt_port = port_info_array[i]
                    break
            if mt_port.empty():
                raise RuntimeError("No MTi device found. Aborting.")

            # Display device details
            did = mt_port.deviceId()
            print(" Device ID: %s" % did.toXsString())
            print(" Port name: %s" % mt_port.portName())

            if not control.openPort(mt_port.portName(), mt_port.baudrate()):
                raise RuntimeError("Could not open port. Aborting.")

            # Get the device object
            device = control.device(did)
            assert(device != 0)
            print("Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString()))

            # Create and attach callback handler to device
            device.addCallbackHandler(self.callback)

            # Put the device into configuration mode before configuring the device
            if not device.gotoConfig():
                raise RuntimeError("Could not put device into configuration mode. Aborting.")

            # Set up the output configuration
            config_array = xda.XsOutputConfigurationArray()
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_PacketCounter, 0))
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_SampleTimeFine, 0))
            # Add IMU configurations
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_Acceleration, 100))
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, 100)) 

            if not device.setOutputConfiguration(config_array):
                raise RuntimeError("Could not configure the device. Aborting.")
            if not device.gotoMeasurement():
                raise RuntimeError("Could not put device into measurement mode. Aborting.")
            if not device.startRecording(): 
                raise RuntimeError("Failed to start recording. Aborting.")
            start_time = xda.XsTimeStamp_nowMs()

            batch_pointer = 0 # keeps track of last processed position
            W = 5 # window size used by zero velocity detector
            speed = 5 # min increase in size before making estimates, has to be >= W
            threshold = 2.20E+08 # Threshold for the ZVD

            # Data collection loop
            while not self.stop:
                current_data_list = np.array(self.callback.getData())
                length = len(current_data_list)
                init = self.ins is None
                if init:
                    if length >= 20:
                        self.ins = INS(current_data_list[:20], sigma_a = 0.00098, sigma_w = 9.20E-05) # initial ins
                        self.processData(current_data_list[:20], W, threshold, init)
                        batch_pointer = 20
                else:
                    if length > batch_pointer+speed: # controls how often make estimates
                        batch_size = (((length - batch_pointer) // W) * W) - 1 # 5n - 1 to account for last value of previous batch
                        self.processData(current_data_list[batch_pointer-1:batch_pointer+batch_size], W, threshold, init)
                        batch_pointer += batch_size
            
            # Stop recording data
            if not device.stopRecording(): 
                raise RuntimeError("Failed to stop recording. Aborting.")

            device.removeCallbackHandler(self.callback)
            control.closePort(mt_port.portName())
            control.close()

            runtime = (xda.XsTimeStamp_nowMs() - start_time) / 1000
            length = self.callback.getLengthData()
            print ("Time: %s seconds" % runtime)
            print ("Datapoints: ", length)

            if trial_type == 'stairs':
                trial_speed = 'stairs'
                trial_type = ''
                name = '_'.join(['stairs',file_name])
            else:
                name = '_'.join([trial_type,trial_speed,file_name])
            # Remaining unprocessed data
            if self.ins is not None and batch_pointer != 0:
                current_data_list = np.array(self.callback.getData())
                self.processData(current_data_list[batch_pointer-1:], W, threshold, False)

                # Save final trajectory graphs
                tools.save_topdown(self.estimates, self.zv, file_name, trial_speed, f'results/graphs/{name}_topdown.png')
                tools.save_vertical(self.estimates, self.zv, file_name, trial_speed, f'results/graphs/{name}_vertical.png')
                print("Topdown graph image created at: "+f'results/graphs/{name}_topdown.png')   
                print("Vertical graph image created at: "+f'results/graphs/{name}_vertical.png')   

            # Save raw data        
            path = os.path.join('data',trial_type,trial_speed,file_name+'.csv')        
            np.savetxt(path, self.callback.getData(), delimiter=",", header="AccX,AccY,AccZ,GyrX,GyrY,GyrZ", comments='')
            print("Raw data CSV file created at: "+path)   

            # Save position and velocity estimates and if stationary
            combined = np.column_stack((self.estimates[:,0:6], self.zv.astype(int)))
            np.savetxt(f"results/estimates/{name}.csv", combined, delimiter=",", header="x,y,z,vx,vy,vz,zv", comments='', fmt="%.15g,%.15g,%.15g,%.15g,%.15g,%.15g,%d")
            print("Estimates CSV file created at: "+f"results/estimates/{name}.csv") 

            self.setStop(False) # Toggle again since toggle was pressed
        except RuntimeError as error:
            print(error)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            self.setRunning(False)  # Ensure running is set to False when the thread ends
