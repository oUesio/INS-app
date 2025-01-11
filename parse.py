import xsensdeviceapi as xda
import time
from threading import Lock

# Callback class to handle device progress updates
class XdaCallback(xda.XsCallback):
    def __init__(self):
        xda.XsCallback.__init__(self)
        self.m_progress = 0 
        self.m_lock = Lock() # Thread lock

    def progress(self):
        return self.m_progress

    def onProgressUpdated(self, dev, current, total, identifier):
        # Update progress value in a thread-safe way
        self.m_lock.acquire()
        self.m_progress = current
        self.m_lock.release()

class Parse:
    def __init__(self):
        self.running = False

    def getRunning(self):
        return self.running
    
    def toggleRunning(self):
        self.running = not self.running

    def main(self, mtb, csv):
        self.toggleRunning()
        # Default values
        if not mtb:
            mtb = "logfile"
        if not csv:
            csv = "exportfileTEMP"

        print("Creating XsControl object...")
        # Create an instance of XsControl
        control = xda.XsControl_construct()
        assert(control != 0)

        # Get and display the Xsens Device API version
        xdaVersion = xda.XsVersion()
        xda.xdaVersion(xdaVersion)
        print("Using XDA version %s" % xdaVersion.toXsString())

        #try:
        logfileName = mtb+".mtb"
        print("Opening log file %s..." % logfileName)
        # Attempt to open the log file
        if not control.openLogFile(logfileName):
            self.toggleRunning()
            raise RuntimeError("Failed to open log file. Aborting.")
        print("Opened log file: %s" % logfileName)

        # Retrieve device IDs from the log file ############
        deviceIdArray = control.mainDeviceIds()
        for i in range(deviceIdArray.size()):
            if deviceIdArray[i].isMti() or deviceIdArray[i].isMtig():
                mtDevice = deviceIdArray[i]
                break

        # Check if an MTi device was found
        if not mtDevice:
            self.toggleRunning()
            raise RuntimeError("No MTi device found. Aborting.")

        # Get the device object
        device = control.device(mtDevice)
        assert(device != 0)

        print("Device: %s, with ID: %s found in file" % (device.productCode(), device.deviceId().toXsString()))

        # Create and attach callback handler to device
        callback = XdaCallback()
        device.addCallbackHandler(callback)

        # By default XDA does not retain data for reading it back.
        # By enabling this option XDA keeps the buffered data in a cache so it can be accessed 
        # through XsDevice::getDataPacketByIndex or XsDevice::takeFirstDataPacketInQueue
        device.setOptions(xda.XSO_RetainBufferedData, xda.XSO_None);

        # Load the log file and wait until it is loaded
        # Wait for logfile to be fully loaded, there are three ways to do this:
        # - callback: Demonstrated here, which has loading progress information
        # - waitForLoadLogFileDone: Blocking function, returning when file is loaded
        # - isLoadLogFileInProgress: Query function, used to query the device if the loading is done
        #
        # The callback option is used here.

        print("Loading the file...")
        # Load the log file
        device.loadLogFile()
        while callback.progress() != 100:
            time.sleep(0)
        print("File is fully loaded")

        # Get total number of samples
        packetCount = device.getDataPacketCount()

        # Export the data
        print("Exporting the data...")
        s = "count,timestamp,AccX,AccY,AccZ,GyrX,GyrY,GyrZ,q0,q1,q2,q3\n"
        index = 0
        while index < packetCount:
            # Retrieve a packet
            packet = device.getDataPacketByIndex(index)
            count = packet.packetCounter()
            s += "%s" % (count)
            timestamp = packet.timeOfArrival()
            s += ",%s" % (timestamp.msTime())
            acc = packet.calibratedAcceleration()
            s += ",%s,%s,%s" % (acc[0],acc[1],acc[2])
            gyr = packet.calibratedGyroscopeData()
            s += ",%s,%s,%s" % (gyr[0],gyr[1],gyr[2])
            quaternion = packet.orientationQuaternion()
            s += ",%s,%s,%s,%s" % (quaternion[0],quaternion[1],quaternion[2],quaternion[3])

            s += "\n" # Add a newline for each packet
            index += 1

        # Save the exported data to a file
        exportFileName = csv+".csv"
        with open(exportFileName, "w") as outfile:
            outfile.write(s)
        print("File is exported to: %s" % exportFileName)

        print("Removing callback handler...")
        device.removeCallbackHandler(callback)

        print("Closing XsControl object...")
        control.close()
        self.toggleRunning()
        ''''
        except RuntimeError as error:
            self.toggleRunning()
            print(error)
        except:
            self.toggleRunning()
            print("An unknown fatal error has occured. Aborting.")
        else:
            self.toggleRunning()
            print("Successful exit.")
        '''
