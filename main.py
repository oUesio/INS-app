from PyQt6.QtCore import QSize, QTimer, QRunnable, pyqtSlot, QThreadPool
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, QLabel, QLineEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from receive import Receive
from parse import Parse
import numpy as np
import matplotlib
import warnings
warnings.simplefilter("ignore", UserWarning)
matplotlib.use('QtAgg')

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            print(f"Worker thread crashed: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rec = Receive()
        self.par = Parse()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(10)
        self.imudata = np.zeros((250, 6))  # Initialize with empty data
        self.estimates = None
        self.zv = None
        self.setFixedSize(QSize(1050, 700))
        self.setWindowTitle("Realtime Foot-mounted INS")

        # Updates the plots
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)

        # Polling the receive running status
        self.check_running_timer = QTimer(self)
        self.check_running_timer.timeout.connect(self.check_rec_running)

        # Buttons and LineEdits
        window1_layout = QHBoxLayout()
        controls_layout = QVBoxLayout()
        receive_layout1 = QGridLayout()
        receive_layout2 = QGridLayout()
        parse_layout1 = QGridLayout()
        parse_layout2 = QGridLayout()
        debug_layout = QGridLayout()

        receive_layout1.addWidget(QLabel("Enter trial type (Default: hallway):"), 0, 0)
        self.receive_input1 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input1, 0, 2)
        receive_layout1.addWidget(QLabel("Enter trial speed (Default: walk):"), 1, 0)
        self.receive_input2 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input2, 1, 2)
        receive_layout1.addWidget(QLabel("Enter CSV file name (Default: exportfile):"), 2, 0)
        self.receive_input3 = QLineEdit(self)
        receive_layout1.addWidget(self.receive_input3, 2, 2)

        receive_button1 = QPushButton("Start Receive")
        receive_button1.clicked.connect(self.start_receive)
        receive_layout2.addWidget(receive_button1, 0, 0)
        receive_button2 = QPushButton("Stop Receive")
        receive_button2.clicked.connect(self.stop_receive)
        receive_layout2.addWidget(receive_button2, 0, 1)

        parse_layout1.addWidget(QLabel("Enter trial type (Default: hallway):"), 0, 0)
        self.parse_input1 = QLineEdit(self)
        parse_layout1.addWidget(self.parse_input1, 0, 2)
        parse_layout1.addWidget(QLabel("Enter trial speed (Default: walk):"), 1, 0)
        self.parse_input2 = QLineEdit(self)
        parse_layout1.addWidget(self.parse_input2, 1, 2)
        parse_layout1.addWidget(QLabel("Enter CSV file name (Default: exportfile):"), 2, 0)
        self.parse_input3 = QLineEdit(self)
        parse_layout1.addWidget(self.parse_input3, 2, 2)

        parse_button = QPushButton("Parse", self)
        parse_button.clicked.connect(self.run_parse)
        parse_layout2.addWidget(parse_button, 0, 0)
        parse_layout2.setColumnStretch(1, 1)  # 2/3 empty space
        parse_layout2.setColumnStretch(0, 1)  # 1/3 occupied by the button

        controls_layout.addLayout(receive_layout1)
        controls_layout.addLayout(receive_layout2)
        controls_layout.addLayout(parse_layout1)
        controls_layout.addLayout(parse_layout2)
        controls_layout.addLayout(debug_layout)

        # Plot
        window2_layout = QHBoxLayout()

        self.canvas1 = MplCanvas(self, width=5.5, height=4, dpi=100)
        window2_layout.addWidget(self.canvas1)
        self.canvas2 = MplCanvas(self, width=5.5, height=4, dpi=100)
        window2_layout.addWidget(self.canvas2)

        window1_layout.addLayout(controls_layout)

        self.canvas3 = MplCanvas(self, width=5.5, height=5, dpi=100)
        window1_layout.addWidget(self.canvas3)

        # Full window
        window1 = QWidget()
        window1.setFixedSize(1050, 350)
        window1.setLayout(window1_layout)

        window2 = QWidget()
        window2.setFixedSize(1050, 350)
        window2.setLayout(window2_layout)

        full_window_layout = QVBoxLayout()
        full_window_layout.addWidget(window1)
        full_window_layout.addWidget(window2)
        full_window = QWidget()
        full_window.setLayout(full_window_layout)

        self.setCentralWidget(full_window)
        self.init_plots()

    def init_plots(self):
        try:
            self.canvas1.axes.set_title("Linear Acceleration")
            self.canvas1.axes.set_ylabel("Acceleration (Gs)")
            self.line1, = self.canvas1.axes.plot([], [], label='x')
            self.line2, = self.canvas1.axes.plot([], [], label='y')
            self.line3, = self.canvas1.axes.plot([], [], label='z')
            self.canvas1.axes.legend()
            self.canvas1.axes.grid()
            self.canvas1.fig.subplots_adjust(left=0.15)

            self.canvas2.axes.set_title("Angular Velocity")
            self.canvas2.axes.set_ylabel("Angular Velocity (deg/s)")
            self.line4, = self.canvas2.axes.plot([], [], label='x')
            self.line5, = self.canvas2.axes.plot([], [], label='y')
            self.line6, = self.canvas2.axes.plot([], [], label='z')
            self.canvas2.axes.legend()
            self.canvas2.axes.grid()
            self.canvas2.fig.subplots_adjust(left=0.15)

            self.canvas3.axes.set_xlabel("x (m)")
            self.canvas3.axes.set_ylabel("y (m)")
            self.scatter_plot = self.canvas3.axes.scatter([], [], color="red", s=30, label="Estimated ZV")
            self.traj_plot, = self.canvas3.axes.plot([], [], linewidth=1.7, color="blue", label="Trajectory")
            self.canvas3.axes.legend()
            self.canvas3.axes.grid()
            self.canvas3.fig.subplots_adjust(bottom=0.18, left=0.15, top=1)
        except Exception as e:
            print(f"Unexpected error (init_plots): {e}")

    def update_raw_plot(self):
        try:
            data = self.imudata[-250:]
            indices = np.arange(len(self.imudata))[-250:]
            
            if data.shape[0] > 0:
                # Accelerometer
                self.line1.set_data(indices, data[:, 0] / 9.8)
                self.line2.set_data(indices, data[:, 1] / 9.8)
                self.line3.set_data(indices, data[:, 2] / 9.8)
                # Gyroscope
                self.line4.set_data(indices, data[:, 3] / 180 / np.pi)
                self.line5.set_data(indices, data[:, 4] / 180 / np.pi)
                self.line6.set_data(indices, data[:, 5] / 180 / np.pi)

                self.canvas1.axes.relim()
                self.canvas1.axes.autoscale_view()
                self.canvas1.draw()

                self.canvas2.axes.relim()
                self.canvas2.axes.autoscale_view()
                self.canvas2.draw()
        except Exception as e:
            print(f"Unexpected error (update_raw_plot): {e}")

    def update_position_plot(self):
        try:
            if self.estimates is not None and self.zv is not None and len(self.estimates) == len(self.zv):
                traj = self.estimates

                traj_true = traj[self.zv]
                self.scatter_plot.set_offsets(np.column_stack((-traj_true[:, 0], traj_true[:, 1])))

                self.traj_plot.set_data(-traj[:, 0], traj[:, 1])

                self.canvas3.axes.relim()
                self.canvas3.axes.autoscale_view()
                self.canvas3.axes.set_aspect('equal', adjustable='datalim')
                self.canvas3.draw()
        except Exception as e:
            print(f"Unexpected error (update_position_plot): {e}")

    def update_data(self):
        try:
            if self.rec.getRunning():
                data_list = self.rec.getRawData()
                estimates, zv = self.rec.getEstimates()
                if estimates is not None and zv is not None:
                    self.estimates, self.zv = estimates, zv
                    self.update_position_plot()
                if data_list: # Empty list
                    self.imudata = np.array(data_list)
                    self.update_raw_plot()
        except Exception as e:
            print(f"Unexpected error (update_data): {e}")

    def start_receive(self):
        try:
            if not self.rec.getRunning() and not self.par.getRunning():
                self.imudata = np.zeros((250, 6))
                self.estimates = None
                self.zv = None
                input1 = self.receive_input1.text()
                input2 = self.receive_input2.text()
                input3 = self.receive_input3.text()
                rec_main = Worker(self.rec.main, input1, input2, input3)
                self.threadpool.start(rec_main)
                self.check_running_timer.start(100)
        except Exception as e:
            print(f"Unexpected error (start_receive): {e}")

    def check_rec_running(self):
        if self.rec.getRunning():
            self.check_running_timer.stop()
            # Waits for receive to start before starting while loop
            self.update_timer.start(20)

    def stop_receive(self):
        try:
            # Only runs if receive is running
            if self.rec.getRunning():
                self.rec.setStop(True)
                self.update_timer.stop()
                print ("\nStopped running")
        except Exception as e:
            print(f"Unexpected error (stop_receive): {e}")

    def run_parse(self):
        if not self.rec.getRunning() and not self.par.getRunning():
            input1 = self.receive_input1.text()
            input2 = self.receive_input2.text()
            input3 = self.receive_input3.text()
            rec_main = Worker(self.par.plot_data, input1, input2, input3)
            self.threadpool.start(rec_main)
            # plot data in gui

app = QApplication([])
window = MainWindow()
window.show()
app.exec()