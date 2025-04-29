from PyQt6.QtCore import QSize, QTimer, QRunnable, pyqtSlot, QThreadPool, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, QLabel, QLineEdit
import pyqtgraph as pg
import numpy as np
from receive import Receive
import warnings
warnings.simplefilter("ignore", UserWarning)

# Testing graph updates
import time #
import matplotlib.pyplot as plt #

pg.setConfigOption('background', 'white')

class CustomPlotWidget(pg.PlotWidget):
    """
    Custom PyQtGraph PlotWidget with black axes, grid, and legend.

    :param title: Title for the plot
    """
    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set axis colors to black
        self.getAxis('left').setPen(pg.mkPen('black'))   
        self.getAxis('bottom').setPen(pg.mkPen('black'))  
        self.getAxis('left').setTextPen(pg.mkPen('black'))  
        self.getAxis('bottom').setTextPen(pg.mkPen('black'))  
        self.setFixedSize(460, 310)
        self.setTitle(f"<span style='color: black; font-size: 12pt;'>{title}</span>")
        self.showGrid(x=True, y=True, alpha=0.5)
        self.addLegend(labelTextColor='k')

class Worker(QRunnable):
    """
    A worker class to run background tasks in a separate thread.

    :param fn: Function to execute
    :param args: Arguments to pass into the function
    :param kwargs: Keyword arguments to pass to the function
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        """Runs the function with arguments in a background thread."""
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Worker thread crashed: {e}")

class MainWindow(QMainWindow):
    """
    Main application window for controlling data reception and displaying real-time IMU 
    data visualisations.

    :ivar rec: Instance of Receive for collecting and processing data
    :ivar threadpool: Thread pool used to manage and execute background tasks concurrently
    :ivar update_timer: Idle time for updating the visualisation plots
    """
    def __init__(self):
        super().__init__()
        self.rec = Receive()
        self.threadpool = QThreadPool() 

        #self.call_counts = [] # Testing graph updates
        #self.start_time = int(time.time())

        self.setFixedSize(QSize(1050, 700))
        self.setWindowTitle("Realtime Foot-mounted INS")

        # Updates the plots
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.updateData)

        # UI Layouts
        window1_layout = QHBoxLayout()
        controls_layout = QVBoxLayout()
        receive_layout1 = QGridLayout()
        receive_layout2 = QGridLayout()
        
        controls_window = QWidget()
        receive_layout1.addWidget(QLabel("Enter trial type (Default: hallway):"), 0, 0)
        self.receive_input1 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input1, 0, 1)
        receive_layout1.addWidget(QLabel("Enter trial speed (Default: walk):"), 1, 0)
        self.receive_input2 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input2, 1, 1)
        receive_layout1.addWidget(QLabel("Enter CSV file name (Default: exportfile):"), 2, 0)
        self.receive_input3 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input3, 2, 1)

        receive_button1 = QPushButton("Start Receive")
        receive_button1.clicked.connect(self.startReceive)
        receive_layout2.addWidget(receive_button1, 0, 0)
        receive_button2 = QPushButton("Stop Receive")
        receive_button2.clicked.connect(self.stopReceive)
        receive_layout2.addWidget(receive_button2, 0, 1)

        controls_layout.addLayout(receive_layout1)
        controls_layout.addLayout(receive_layout2)
        controls_window.setLayout(controls_layout)
        controls_window.setFixedSize(460, 310)

        # PyQtGraph Plots
        self.plotWidget1 = CustomPlotWidget(title="Linear Acceleration")
        self.plotWidget1.setLabel('left', 'Acceleration (Gs)')
        self.line1 = self.plotWidget1.plot([], [], pen=pg.mkPen(color='#1f77b4', width=2), name='x')
        self.line2 = self.plotWidget1.plot([], [], pen=pg.mkPen(color='#ff7f0e', width=2), name='y')
        self.line3 = self.plotWidget1.plot([], [], pen=pg.mkPen(color='#2ca02c', width=2), name='z')

        self.plotWidget2 = CustomPlotWidget(title="Angular Velocity")
        self.plotWidget2.setLabel('left', 'Angular Velocity (deg/s)')
        self.line4 = self.plotWidget2.plot([], [], pen=pg.mkPen(color='#1f77b4', width=2), name='x')
        self.line5 = self.plotWidget2.plot([], [], pen=pg.mkPen(color='#ff7f0e', width=2), name='y')
        self.line6 = self.plotWidget2.plot([], [], pen=pg.mkPen(color='#2ca02c', width=2), name='z')

        self.plotWidget3 = CustomPlotWidget(title="Trajectory")
        self.plotWidget3.setLabel('bottom', 'x (m)')
        self.plotWidget3.setLabel('left', 'y (m)')
        self.scatter_plot = pg.ScatterPlotItem()
        self.traj_plot = self.plotWidget3.plot([], [], pen=pg.mkPen(color='blue', width=2), name="Trajectory")
        self.scatter_legend_item = self.plotWidget3.plot([], [], pen=pg.mkPen(width=3, color='r'), name="Estimated ZV")
        self.plotWidget3.addItem(self.scatter_plot)
        self.plotWidget3.enableAutoRange()
        self.plotWidget3.getViewBox().setAspectLocked(True)

        # Layout arrangement
        window2_layout = QHBoxLayout()
        window2_layout.addWidget(self.plotWidget1)
        window2_layout.addWidget(self.plotWidget2)
        window2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        window1_layout.addWidget(controls_window)
        window1_layout.addWidget(self.plotWidget3)
        window1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set layouts to widgets
        window1 = QWidget()
        window1.setFixedSize(1050, 350)
        window1.setLayout(window1_layout)
        window2 = QWidget()
        window2.setFixedSize(1050, 350)
        window2.setLayout(window2_layout)
        full_window_layout = QVBoxLayout()
        full_window_layout.addWidget(window1)
        full_window_layout.addWidget(window2)
        full_window_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full_window = QWidget()
        full_window.setLayout(full_window_layout)
        self.setCentralWidget(full_window)

    def updateRawPlots(self, imudata):
        """
        Update linear acceleration and angular velocity plots with new IMU data.

        :param imudata: Array of accelerometer and gyroscope data
        """
        try:
            data = imudata[-250:]
            indices = np.arange(len(imudata))[-250:]
            
            if data.shape[0] > 0:
                self.line1.setData(indices, data[:, 0] / 9.8)
                self.line2.setData(indices, data[:, 1] / 9.8)
                self.line3.setData(indices, data[:, 2] / 9.8)
                self.line4.setData(indices, data[:, 3] / 180 / np.pi)
                self.line5.setData(indices, data[:, 4] / 180 / np.pi)
                self.line6.setData(indices, data[:, 5] / 180 / np.pi)
        except Exception as e:
            print(f"Error (updateRawPlots): {e}")

    def updatePositionPlot(self, estimates, zv):
        """
        Update trajectory plot and zero-velocity scatter markers.

        :param estimates: Array of estimated states from the INS
        :param zv: Zero velocity detection flags
        """
        try:
            traj_true = estimates[zv]
            self.scatter_plot.setData(-traj_true[:, 0], traj_true[:, 1], pen=pg.mkPen(width=3, color='r'), symbol='o', name="Estimated ZV")
            self.traj_plot.setData(-estimates[:, 0], estimates[:, 1])
        except Exception as e:
            print(f"Error (updatePositionPlot): {e}")

    def updateData(self):
        """
        Called at regular intervals to update both raw sensor plots and position trajectory.
        """
        try:
            if self.rec.getRunning():
                data_list = self.rec.getRawData()
                estimates, zv = self.rec.getEstimates()
                if estimates is not None and zv is not None:

                    #current_time = int(time.time()) - self.start_time # Testing graph updates
                    #while len(self.call_counts) <= current_time:
                    #    self.call_counts.append(0)
                    #self.call_counts[current_time] += 1

                    # Make the same size
                    min_len = min(len(estimates), len(zv))
                    estimates = estimates[:min_len]
                    zv = zv[:min_len]
                    self.updatePositionPlot(estimates, zv)
                if data_list: # Empty list
                    self.updateRawPlots(np.array(data_list))
        except Exception as e:
            print(f"Error (updateData): {e}")

    def startReceive(self):
        """
        Starts receiving IMU data by running Receive's main method and also starts the 
        data update timer to start visualising the data.
        """
        try:
            if not self.rec.getRunning():
                input1 = self.receive_input1.text()
                input2 = self.receive_input2.text()
                input3 = self.receive_input3.text()
                if input1 not in ['','hallway', 'stairs']:
                    raise RuntimeError("Invalid trial type (hallway, stairs). Aborting.")
                if input1 in ['','hallway'] and input2 not in ['', 'walk', 'run', 'mixed']:
                    raise RuntimeError("Invalid trial speed for hallway (walk, run, mixed). Aborting.")
                rec_main = Worker(self.rec.main, input1, input2, input3)
                self.threadpool.start(rec_main)
                self.update_timer.start(20)
        except Exception as e:
            print(f"Error (startReceive): {e}")

    def stopReceive(self):
        """
        Stops receiving data and stops the update timer.
        """
        try:
            # Only runs if receive is running
            if self.rec.getRunning():
                self.rec.setStop(True)
                self.update_timer.stop()
                print ("\nStopped running")

                #plt.figure(figsize=(16, 4)) # Testing graph updates
                #plt.plot(self.call_counts, linestyle='-', color='m')
                #plt.xlabel('Seconds')
                #plt.ylabel('Graph Updates')
                #plt.grid()
                #plt.savefig('update_rate.png', dpi=400, bbox_inches='tight')   
        except Exception as e:
            print(f"Error (stopReceive): {e}")

# Runs the application
app = QApplication([])
window = MainWindow()
window.show()
app.exec()
