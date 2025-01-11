import sys
import xsensdeviceapi as xda
from threading import Lock
import csv

# Callback class to handle live data from the device
class XdaCallback(xda.XsCallback):
    def __init__(self, max_buffer_size = 5):
        xda.XsCallback.__init__(self)
        self.m_maxNumberOfPacketsInBuffer = max_buffer_size # Max buffer size for storing packets
        self.m_packetBuffer = list() # Buffer to store data packets
        self.data_list = [] 
        self.m_lock = Lock() # Thread lock

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
        count = packet.packetCounter()
        timestamp = packet.timeOfArrival()
        acc = packet.calibratedAcceleration()
        gyr = packet.calibratedGyroscopeData()
        quaternion = packet.orientationQuaternion()
        data = {
                "count": count,
                "timestamp": timestamp.msTime(),
                "AccX": acc[0],
                "AccY": acc[1],
                "AccZ": acc[2],
                "GyrX": gyr[0],
                "GyrY": gyr[1],
                "GyrZ": gyr[2],
                "q0": quaternion[0],
                "q1": quaternion[1],
                "q2": quaternion[2],
                "q3": quaternion[3]
            }
        self.data_list.append(data) 
        #print(data)
        while len(self.m_packetBuffer) >= self.m_maxNumberOfPacketsInBuffer:
            self.m_packetBuffer.pop() # Remove the oldest packet if buffer is full
        self.m_packetBuffer.append(xda.XsDataPacket(packet)) # Add the new packet to the buffer
        self.m_lock.release()

    def getLengthData(self):
        return len(self.data_list)

class Receive:
    def __init__(self):
        self.stop = False
        self.running = False

    def getStop(self):
        return self.stop
    
    def getRunning(self):
        return self.running

    def toggleStop(self):
        self.stop = not self.stop

    def toggleRunning(self):
        self.running = not self.running

    def main(self, mtbName, csvName):
        self.toggleRunning()
        # Default values
        if not mtbName:
            mtbName = "logfile"
        if not csvName:
            csvName = "exportfile"

        # Create XsControl object
        control = xda.XsControl_construct()
        assert(control != 0)

        ####################
        xdaVersion = xda.XsVersion()
        xda.xdaVersion(xdaVersion)
        print("Using XDA version %s" % xdaVersion.toXsString())
        ####################

        try:
            # Scan for connected Xsens devices
            portInfoArray =  xda.XsScanner_scanPorts() 
            # Find an MTi device
            mtPort = xda.XsPortInfo()
            for i in range(portInfoArray.size()):
                if portInfoArray[i].deviceId().isMti() or portInfoArray[i].deviceId().isMtig():
                    mtPort = portInfoArray[i]
                    break
            if mtPort.empty():
                self.toggleRunning()
                raise RuntimeError("No MTi device found. Aborting.")

            ####################
            # Display device details
            did = mtPort.deviceId()
            print(" Device ID: %s" % did.toXsString())
            print(" Port name: %s" % mtPort.portName())
            ####################

            # Open the communication port for the device
            if not control.openPort(mtPort.portName(), mtPort.baudrate()):
                self.toggleRunning()
                raise RuntimeError("Could not open port. Aborting.")

            ####################
            # Get the device object
            device = control.device(did)
            assert(device != 0)
            print("Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString()))
            ####################

            # Create and attach callback handler to device
            callback = XdaCallback()
            device.addCallbackHandler(callback)

            # Put the device into configuration mode before configuring the device
            if not device.gotoConfig():
                self.toggleRunning()
                raise RuntimeError("Could not put device into configuration mode. Aborting.")

            # Set up the output configuration
            configArray = xda.XsOutputConfigurationArray()
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_PacketCounter, 0))
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_SampleTimeFine, 0))
            # Add IMU configurations
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_Acceleration, 100))
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, 100))

            # Apply the output configuration
            if not device.setOutputConfiguration(configArray):
                self.toggleRunning()
                raise RuntimeError("Could not configure the device. Aborting.")

            # Create a log file to store recorded data
            logFileName = mtbName+".mtb"
            if device.createLogFile(logFileName) != xda.XRV_OK:
                self.toggleRunning()
                raise RuntimeError("Failed to create a log file. Aborting.")

            # Put the device into measurement mode
            if not device.gotoMeasurement():
                self.toggleRunning()
                raise RuntimeError("Could not put device into measurement mode. Aborting.")

            # Start recording data
            if not device.startRecording(): 
                self.toggleRunning()
                raise RuntimeError("Failed to start recording. Aborting.")
            ####################
            startTime = xda.XsTimeStamp_nowMs()
            ####################

            # Main loop to control how long the device is being recorded
            while not self.stop:
                print ("Still running...")
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
                self.toggleRunning()
                raise RuntimeError("Failed to close log file. Aborting.")
            # Remove callback handler
            device.removeCallbackHandler(callback)
            # Close the port
            control.closePort(mtPort.portName())
            # Close XsControl object
            control.close()

            ####################
            runtime = (xda.XsTimeStamp_nowMs() - startTime) / 1000
            length = callback.getLengthData()
            print ("Time: %s seconds" % runtime)
            print ("Datapoints: ", length)
            print ("Frequency: ", round(length / runtime, 2))
            ####################

            #######################
            csvFileName = csvName+".csv"
            keys = callback.data_list[0].keys()
            with open(csvFileName, "w") as outfile:
                dict_writer = csv.DictWriter(outfile, keys)
                dict_writer.writeheader()
                dict_writer.writerows(callback.data_list)
            print("CSV file created: %s" % csvFileName)
            print("Log file created: %s" % logFileName)
            #######################

            self.toggleRunning()
            self.toggleStop()
        except RuntimeError as error:
            self.toggleRunning()
            print(error)
            sys.exit(1)
        except:
            print("An unknown fatal error has occured. Aborting.")
            self.toggleRunning()
            sys.exit(1)
