from tkinter import *
from receive import Receive
from parse import Parse
from threading import Thread
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
#############
import threading

class INS_App():
    def __init__(self):
        self.rec = Receive()
        self.par = Parse()
        self.imudata = np.zeros((250, 6))  # Initialize with empty data
        
        self.window = Tk()
        self.window.geometry('1000x900')
        self.window.title("INS App")
        
        canvas = FigureCanvasTkAgg(plt.gcf(), master=self.window)
        canvas.get_tk_widget().grid(row=14, column=0)
        # Create two subplots in row 1 and column 1, 2
        plt.gcf().subplots(1, 2)
        ani = FuncAnimation(plt.gcf(), self.plot_acc_gyr, interval=1000, blit=False)

        Label(self.window, text="Enter trial type (Default: hallway):").grid(row=1, column=0, padx=3, pady=2)
        self.receive_input1 = Entry(self.window, width=30)
        self.receive_input1.grid(row=1, column=1, padx=3, pady=2)

        Label(self.window, text="Enter trial speed (Default: walk):").grid(row=2, column=0, padx=3, pady=2)
        self.receive_input2 = Entry(self.window, width=30)
        self.receive_input2.grid(row=2, column=1, padx=3, pady=2)

        Label(self.window, text="Enter CSV file name (Default: exportfile):").grid(row=3, column=0, padx=3, pady=2)
        self.receive_input3 = Entry(self.window, width=30)
        self.receive_input3.grid(row=3, column=1, padx=3, pady=2)

        receive_button1 = Button(self.window, text="Start Receive", command=self.start_receive)
        receive_button1.grid(row=4, column=0, padx=1, pady=2)

        receive_button2 = Button(self.window, text="Stop Receive", command=self.stop_receive)
        receive_button2.grid(row=4, column=1, padx=1, pady=2)

        log_stationary = Button(self.window, text="Log Zero-Velocity", command=self.log_zv)
        log_stationary.grid(row=4, column=2, padx=1, pady=2)

        # Parse section
        Label(self.window, text="Enter trial type (Default: hallway):").grid(row=5, column=0, padx=3, pady=21)
        self.parse_input1 = Entry(self.window, width=30)
        self.parse_input1.grid(row=5, column=1, padx=1, pady=2)

        Label(self.window, text="Enter trial speed (Default: walk):").grid(row=6, column=0, padx=3, pady=2)
        self.parse_input2 = Entry(self.window, width=30)
        self.parse_input2.grid(row=6, column=1, padx=1, pady=2)

        Label(self.window, text="Enter CSV file name (Default: exportfile):").grid(row=7, column=0, padx=3, pady=2)
        self.parse_input3 = Entry(self.window, width=30)
        self.parse_input3.grid(row=7, column=1, padx=1, pady=2)

        parse_button = Button(self.window, text="Parse", command=self.run_parse)
        parse_button.grid(row=8, column=0)

        debug_button1 = Button(self.window, text="DEBUG count threads", command=self.active_count)
        debug_button1.grid(row=9, column=0)

        debug_button2 = Button(self.window, text="DEBUG enum threads", command=self.enum_threads)
        debug_button2.grid(row=9, column=1)

        self.window.mainloop()


    def update_data(self):
        while self.rec.getRunning():
            data_list = self.rec.getData()
            if data_list:
                self.imudata = np.array(data_list)

    def start_receive(self):
        if not self.rec.getRunning() and not self.par.getRunning():
            input1 = self.receive_input1.get()
            input2 = self.receive_input2.get()
            input3 = self.receive_input3.get()
            Thread(target=self.rec.main, args=(input1, input2, input3), daemon=True).start()
            Thread(target=self.update_data, daemon=True).start()

    def stop_receive(self):
        # Only runs if receive is running
        if self.rec.getRunning():
            print (str(self.rec.getRunning()))
            self.rec.toggleStop()
            print ("\nStopped running")

    def log_zv(self):
        if self.rec.getRunning():
            self.rec.toggleZV()
            print ("\nLogged Zero-velocity")

    def run_parse(self):
        if not self.rec.getRunning() and not self.par.getRunning():
            input1 = self.receive_input1.get()
            input2 = self.receive_input2.get()
            input3 = self.receive_input3.get()
            Thread(target=self.par.plot_data, args=(input1, input2, input3), daemon=True).start()
    
    def active_count(self):
        print (threading.active_count())

    def enum_threads(self):
        for thread in threading.enumerate(): 
            print(thread.name)

    def plot_acc_gyr(self, i):
        # Get all axes of figure
        ax1, ax2 = plt.gcf().get_axes()
        # Clear current data
        ax1.cla()
        ax2.cla()
        data = self.imudata[-250:]
        indices = np.arange(len(self.imudata))[-250:]
        # Plot new data
        ax1.plot(indices, data[:,0]/9.8, label='x')
        ax1.plot(indices, data[:,1]/9.8, label='y')
        ax1.plot(indices, data[:,2]/9.8, label='z')
        ax1.set_title('Linear Acceleration')
        ax1.set_ylabel('Linear Acceleration (Gs)')
        ax1.legend()
        ax1.grid()

        ax2.plot(indices, data[:,3]*180/np.pi, label='x')
        ax2.plot(indices, data[:,4]*180/np.pi, label='y')
        ax2.plot(indices, data[:,5]*180/np.pi, label='z')
        ax2.set_title('Angular Velocity')
        ax2.set_ylabel('Angular Velocity (deg/s)')
        ax2.legend()
        ax2.grid()

if __name__ == '__main__':
    INS_App() 
