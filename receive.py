import sys
import numpy as np
import xsensdeviceapi as xda
from threading import Lock
import os
import tools
from ins_tools.util import *
import ins_tools.visualize as visualize
from ins_tools.INS import INS

# Callback class to handle live data from the device
class XdaCallback(xda.XsCallback):
    def __init__(self, max_buffer_size = 5):
        xda.XsCallback.__init__(self)
        self.m_maxNumberOfPacketsInBuffer = max_buffer_size # Max buffer size for storing packets
        self.m_packetBuffer = list() # Buffer to store data packets
        self.m_lock = Lock() # Thread lock
        self.data_list = [] 
        self.zv = False
        self.log_zv = [0]

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
        count = packet.packetCounter() ####
        acc = packet.calibratedAcceleration()
        gyr = packet.calibratedGyroscopeData()

        data = {
                "AccX": acc[0],
                "AccY": acc[1],
                "AccZ": acc[2],
                "GyrX": gyr[0],
                "GyrY": gyr[1],
                "GyrZ": gyr[2],
            }
        
        self.data_list.append(data) 
        #print(data)

        if self.zv: ####
            self.log_zv.append(count) ####
            self.zv = not self.zv ####

        while len(self.m_packetBuffer) >= self.m_maxNumberOfPacketsInBuffer:
            self.m_packetBuffer.pop() # Remove the oldest packet if buffer is full
        self.m_packetBuffer.append(xda.XsDataPacket(packet)) # Add the new packet to the buffer
        self.m_lock.release()

    def getLengthData(self):
        return len(self.data_list)
    
    def toggleZV(self):
        self.m_lock.acquire()
        self.zv = not self.zv
        self.m_lock.release()

class Receive:
    def __init__(self):
        self.stop = False
        self.running = False
        self.callback = None #### DELETE IF REMOVE MANUALLY LOG STATIONARY PHASE

    def getStop(self):
        return self.stop
    
    def getRunning(self):
        return self.running

    def toggleStop(self):
        self.stop = not self.stop

    def toggleRunning(self):
        self.running = not self.running
    
    def toggleZV(self): ####
        self.callback.toggleZV() ####

    def main(self, trial_type, trial_speed, file_name):
        self.toggleRunning()
        self.callback = XdaCallback() #### RESETS OR INITS THE OBJECT
        # Default values
        if not trial_type:
            trial_type = "hallway"
        if not trial_speed:
            trial_speed = "walk"
        if not file_name:
            file_name = "exportfile"

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

            # Open the communication port for the device
            print (mt_port.portName())
            print (mt_port.baudrate()) # 115200 bps
            temp = [xda.XBR_230k4, xda.XBR_460k8, xda.XBR_921k6 , xda.XBR_2000k , xda.XBR_3500k , xda.XBR_4000k]
            '''
            for x in temp:
                print (x)
                print (str(x) + ': ' + str(control.openPort(mt_port.portName(), x)))
                '''

            #return
            if not control.openPort(mt_port.portName(), mt_port.baudrate()):
                raise RuntimeError("Could not open port. Aborting.")

            ####################
            # Get the device object
            device = control.device(did)
            assert(device != 0)
            print("Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString()))
            ####################

            # Create and attach callback handler to device
            # callback = XdaCallback() #### UNCOMMENT AND REPLACE ALL SELF.CALLBACK 
            device.addCallbackHandler(self.callback)

            # Put the device into configuration mode before configuring the device
            if not device.gotoConfig():
                raise RuntimeError("Could not put device into configuration mode. Aborting.")

            # Set up the output configuration
            config_array = xda.XsOutputConfigurationArray()
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_PacketCounter, 0))
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_SampleTimeFine, 0))
            # Add IMU configurations
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_Acceleration, 200))
            config_array.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, 200))

            # Apply the output configuration
            if not device.setOutputConfiguration(config_array):
                raise RuntimeError("Could not configure the device. Aborting.")

            # Put the device into measurement mode
            if not device.gotoMeasurement():
                raise RuntimeError("Could not put device into measurement mode. Aborting.")

            # Start recording data
            if not device.startRecording(): 
                raise RuntimeError("Failed to start recording. Aborting.")
            ####################
            start_time = xda.XsTimeStamp_nowMs()
            ####################

            # Main loop to control how long the device is being recorded
            while not self.stop:
                #print ("Still running...")
                pass  
            
            '''
            while xda.XsTimeStamp_nowMs() - startTime <= 10000:
                pass
            '''

            # Stop recording data
            if not device.stopRecording(): 
                self.toggleRunning()
                raise RuntimeError("Failed to stop recording. Aborting.")

            # Close the log file
            if not device.closeLogFile():
                raise RuntimeError("Failed to close log file. Aborting.")
            # Remove callback handler
            device.removeCallbackHandler(self.callback)
            # Close the port
            control.closePort(mt_port.portName())
            # Close XsControl object
            control.close()

            ####################
            runtime = (xda.XsTimeStamp_nowMs() - start_time) / 1000
            length = self.callback.getLengthData()
            print ("Time: %s seconds" % runtime)
            print ("Datapoints: ", length)
            print ("Frequency: ", round(length / runtime, 2))
            ####################

            tools.export_csv(os.path.join('data',trial_type,trial_speed,file_name), self.callback.data_list)
            print("CSV file created: "+file_name+'.csv')

            with open('test_zv.csv',"w", newline="") as file: ####
                writer = csv.writer(file) ####
                writer.writerow(["count"])  ####
                for value in self.callback.log_zv: ####
                    writer.writerow([value]) ####
            print("CSV file created: test_zv.csv") ####

            self.toggleStop() # Toggle again since toggle was pressed
        except RuntimeError as error:
            print(error)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            self.toggleRunning()  # Ensure running is set to False when the thread ends
            print("Receive thread has ended.")