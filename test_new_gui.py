from PyQt6.QtCore import QSize, QTimer, pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, QLabel, QLineEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from receive import Receive
from parse import Parse
import numpy as np
import matplotlib
import time
matplotlib.use('QtAgg')
#############
import threading

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
        self.fn(*self.args, **self.kwargs)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rec = Receive()
        self.par = Parse()
        self.threadpool = QThreadPool()

        self.imudata = np.zeros((250, 6))  # Initialize with empty data
        self.setFixedSize(QSize(1050, 700))
        self.setWindowTitle("Simple GUI")

        # Buttons and LineEdits
        window1_layout = QVBoxLayout()
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
        log_stationary = QPushButton("Log Zero-Velocity")
        log_stationary.clicked.connect(self.log_zv)
        receive_layout2.addWidget(log_stationary, 0, 2)

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
        parse_layout2.setColumnStretch(1, 2)  # 2/3 empty space
        parse_layout2.setColumnStretch(0, 1)  # 1/3 occupied by the button

        debug_button1 = QPushButton("DEBUG count threads", self)
        debug_button1.clicked.connect(self.active_count)
        debug_layout.addWidget(debug_button1, 0, 1)

        debug_button2 = QPushButton("DEBUG enum threads", self)
        debug_button2.clicked.connect(self.enum_threads)
        debug_layout.addWidget(debug_button2, 0, 3)

        window1_layout.addLayout(receive_layout1)
        window1_layout.addLayout(receive_layout2)
        window1_layout.addLayout(parse_layout1)
        window1_layout.addLayout(parse_layout2)
        window1_layout.addLayout(debug_layout)

        # Plot
        window2_layout = QHBoxLayout()

        self.canvas1 = MplCanvas(self, width=4.5, height=4, dpi=100)
        window2_layout.addWidget(self.canvas1)
        self.canvas2 = MplCanvas(self, width=4.5, height=4, dpi=100)
        window2_layout.addWidget(self.canvas2)

        # Full window
        window1 = QWidget()
        window1.setFixedSize(500, 350)
        window1.setLayout(window1_layout)

        window2 = QWidget()
        window2.setFixedSize(700, 350)
        window2.setLayout(window2_layout)

        full_window_layout = QVBoxLayout()
        full_window_layout.addWidget(window1)
        full_window_layout.addWidget(window2)
        full_window = QWidget()
        full_window.setLayout(full_window_layout)

        self.setCentralWidget(full_window)

    def update_plot(self):
        data = self.imudata[-250:]
        indices = np.arange(len(self.imudata))[-250:]
        self.canvas1.axes.cla()
        self.canvas1.axes.plot(indices, data[:,0]/9.8, label='x')
        self.canvas1.axes.plot(indices, data[:,1]/9.8, label='y')
        self.canvas1.axes.plot(indices, data[:,2]/9.8, label='z')
        self.canvas1.axes.set_title('Linear Acceleration')
        self.canvas1.axes.set_ylabel('Linear Acceleration (Gs)')
        self.canvas1.fig.subplots_adjust(left=0.25)
        self.canvas1.axes.legend()
        self.canvas1.axes.grid()
        self.canvas1.draw()

        self.canvas2.axes.cla()
        self.canvas2.axes.plot(indices, data[:,3]/180/np.pi, label='x')
        self.canvas2.axes.plot(indices, data[:,4]/180/np.pi, label='y')
        self.canvas2.axes.plot(indices, data[:,5]/180/np.pi, label='z')
        self.canvas2.axes.set_title('Angular Velocity')
        self.canvas2.axes.set_ylabel('Angular Velocity (deg/s)')
        self.canvas1.fig.subplots_adjust(left=0.25)
        self.canvas2.axes.legend()
        self.canvas2.axes.grid()
        self.canvas2.draw()

    def update_data(self): 
        while self.rec.getRunning():
            data_list = self.rec.getData()
            if data_list:
                self.imudata = np.array(data_list)
                print (len(self.imudata))
                self.update_plot()
            time.sleep(0.25)
            
    def start_receive(self):
        if not self.rec.getRunning() and not self.par.getRunning():
            input1 = self.receive_input1.text()
            input2 = self.receive_input2.text()
            input3 = self.receive_input3.text()
            rec_main = Worker(self.rec.main, input1, input2, input3)
            self.threadpool.start(rec_main)
            update = Worker(self.update_data) # NOT ALWAYS RUN FOR SOME REASON
            self.threadpool.start(update)

    def stop_receive(self):
        # Only runs if receive is running
        if self.rec.getRunning():
            print (str(self.rec.getRunning()))
            self.rec.toggleStop()
            print ("\nStopped running")

    def log_zv(self):
        pass
        '''if self.rec.getRunning():
            self.rec.toggleZV()
            print ("\nLogged Zero-velocity")'''

    def run_parse(self):
        pass
        '''if not self.rec.getRunning() and not self.par.getRunning():
            input1 = self.receive_input1.text()
            input2 = self.receive_input2.text()
            input3 = self.receive_input3.text()
            Thread(target=self.par.plot_data, args=(input1, input2, input3), daemon=True).start()'''

    def active_count(self):
        print (threading.active_count())

    def enum_threads(self):
        for thread in threading.enumerate(): 
            print(thread.name)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()