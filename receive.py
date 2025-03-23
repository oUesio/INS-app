import sys
import numpy as np
import xsensdeviceapi as xda
from threading import Lock
import os
from ins_tools.util import *
import realtime
from ins_tools.INS_realtime import INS
import tools

# Callback class to handle live data from the device
class XdaCallback(xda.XsCallback):
    def __init__(self, max_buffer_size = 5):
        xda.XsCallback.__init__(self)
        self.m_maxNumberOfPacketsInBuffer = max_buffer_size # Max buffer size for storing packets
        self.m_packetBuffer = list() # Buffer to store data packets
        self.m_lock = Lock() # Thread lock
        self.data_list = [] 

    def packetAvailable(self):
        # Check if there are packets available in the buffer
        self.m_lock.acquire()
        res = len(self.m_packetBuffer) > 0 # Return True if buffer is not empty
        self.m_lock.release()
        return res

    def getNextPacket(self):
        # Retrieve the oldest packet from the buffer
        self.m_lock.acquire()
        assert(len(self.m_packetBuffer) > 0)
        oldest_packet = xda.XsDataPacket(self.m_packetBuffer.pop(0)) # Remove and return the oldest packet
        self.m_lock.release()
        return oldest_packet

    def onLiveDataAvailable(self, dev, packet):
        # Handle live data packets as they become available
        self.m_lock.acquire()
        assert(packet != 0) # Ensure the packet is valid
        acc = packet.calibratedAcceleration()
        gyr = packet.calibratedGyroscopeData()
        
        data = list(acc)+list(gyr)
        self.data_list.append(data) 

        while len(self.m_packetBuffer) >= self.m_maxNumberOfPacketsInBuffer:
            self.m_packetBuffer.pop() # Remove the oldest packet if buffer is full
        self.m_packetBuffer.append(xda.XsDataPacket(packet)) # Add the new packet to the buffer
        self.m_lock.release()

    def getLengthData(self):
        return len(self.data_list)

    def getData(self):
        return self.data_list

class Receive:
    def __init__(self):
        self.stop = False
        self.running = False
        self.callback = XdaCallback() 
        self.realtime = None
        self.estimates = None
        self.zv = None

    def getStop(self):
        return self.stop
    
    def getRunning(self):
        return self.running

    def setStop(self, state):
        self.stop = state

    def setRunning(self, state):
        self.running = state

    def getRawData(self):
        return self.callback.data_list
    
    def getEstimates(self):
        return self.estimates, self.zv

    def main(self, trial_type, trial_speed, file_name):
        self.callback = XdaCallback() # Resets callback
        self.realtime = None # resets realtime
        # Default values
        if not trial_type:
            trial_type = "hallway"
        if not trial_speed:
            trial_speed = "walk"
        if not file_name:
            file_name = "exportfile"
        if trial_type not in ['hallway', 'stairs']:
            raise RuntimeError("Invalid trial type (hallway, stairs). Aborting.")
        if trial_type == 'hallway' and trial_speed not in ['walk', 'run']:
            raise RuntimeError("Invalid trial speed for hallway (walk, run). Aborting.")

        # Create XsControl object
        control = xda.XsControl_construct()
        assert(control != 0)

        ####################
        xda_version = xda.XsVersion()
        xda.xdaVersion(xda_version)
        print("Using XDA version %s" % xda_version.toXsString())
        ####################

        try:
            # Scan for connected Xsens devices
            port_info_array =  xda.XsScanner_scanPorts() 
            print (port_info_array)
            # Find an MTi device
            mt_port = xda.XsPortInfo()
            for i in range(port_info_array.size()):
                if port_info_array[i].deviceId().isMti() or port_info_array[i].deviceId().isMtig():
                    mt_port = port_info_array[i]
                    break
            if mt_port.empty():
                raise RuntimeError("No MTi device found. Aborting.")

            ####################
            # Display device details
            did = mt_port.deviceId()
            print(" Device ID: %s" % did.toXsString())
            print(" Port name: %s" % mt_port.portName())
            ####################

            if not control.openPort(mt_port.portName(), mt_port.baudrate()):
                raise RuntimeError("Could not open port. Aborting.")

            ####################
            # Get the device object
            device = control.device(did)
            assert(device != 0)
            print("Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString()))
            ####################

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
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, 100)) # ???

            if not device.setOutputConfiguration(config_array):
                raise RuntimeError("Could not configure the device. Aborting.")
            if not device.gotoMeasurement():
                raise RuntimeError("Could not put device into measurement mode. Aborting.")
            if not device.startRecording(): 
                raise RuntimeError("Failed to start recording. Aborting.")
            ####################
            start_time = xda.XsTimeStamp_nowMs()
            ####################

            # Main loop
            self.setRunning(True)
            batch_pointer = 0 # keeps track of last processed position
            W = 5 # window size used by zero velocity detector
            speed = 50 # min increase in size before making estimates
            while not self.stop:
                current_data_list = np.array(self.callback.data_list)
                length = len(current_data_list)
                if length > batch_pointer+speed: # controls how often make estimates
                    init = self.realtime is None
                    batch_size = (((length - batch_pointer) // W) * W) - (not init) # 5n size if initial, 5n - 1 to account for last value of previous batch
                    print (batch_size)
                    if init:
                        self.realtime = realtime.RealTime(INS(current_data_list[:batch_size], sigma_a = 0.00098, sigma_w = 9.20E-05), W, 2.20E+08) # initial ins
                    batch_estimates, batch_zv = self.realtime.estimates(current_data_list[batch_pointer-(not init):batch_pointer+batch_size], init) 
                    # resets if it had values from before
                    self.estimates = batch_estimates if init else np.concatenate((self.estimates, batch_estimates)) # extra first value already removed
                    self.zv = batch_zv if init else np.concatenate((self.zv, batch_zv))
                    batch_pointer += batch_size
            
            # Stop recording data
            if not device.stopRecording(): 
                raise RuntimeError("Failed to stop recording. Aborting.")

            device.removeCallbackHandler(self.callback)
            control.closePort(mt_port.portName())
            control.close()

            if trial_type == 'stairs':
                trial_speed = 'stairs'
                name = '_'.join([trial_type,file_name])
            else:
                name = '_'.join([trial_type,trial_speed,file_name])
            # Remaining unprocessed data
            if self.realtime is not None and batch_pointer != 0:
                current_data_list = np.array(self.callback.data_list)
                final_estimates, final_zv = self.realtime.estimates(current_data_list[batch_pointer-1:], init) 
                self.estimates = np.concatenate((self.estimates, final_estimates))
                self.zv = np.concatenate((self.zv, final_zv))

                # Save final trajectory graphs
                tools.save_topdown(self.estimates, self.zv, file_name, trial_speed, f'results/graphs/{name}_topdown.png')
                tools.save_vertical(self.estimates, self.zv, file_name, trial_speed, f'results/graphs/{name}_vertical.png')

            ####################
            runtime = (xda.XsTimeStamp_nowMs() - start_time) / 1000
            length = self.callback.getLengthData()
            print ("Time: %s seconds" % runtime)
            print ("Datapoints: ", length)
            print ("Frequency: ", round(length / runtime, 2))
            ####################

            # Save raw data                
            with open(os.path.join('data',trial_type,trial_speed,file_name+'.csv'),"w", newline="") as file: ####
                writer = csv.writer(file)
                writer.writerow(['AccX','AccY','AccZ','GyrX','GyrY','GyrZ'])
                writer.writerows(self.callback.data_list)
            print("CSV file created: "+file_name+'.csv')   

            # Save position and velocity estimates and if stationary
            combined = np.column_stack((self.estimates[:,0:6], self.zv.astype(int)))
            np.savetxt(f"results/estimates/{name}.csv", combined, delimiter=",", header="x,y,z,vx,vy,vz,zv", comments='', fmt="%.15g,%.15g,%.15g,%.15g,%.15g,%.15g,%d")

            self.setStop(False) # Toggle again since toggle was pressed
        except RuntimeError as error:
            print(error)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            self.setRunning(False)  # Ensure running is set to False when the thread ends
            print("Receive thread has ended.")