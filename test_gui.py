from tkinter import *
from receive import Receive
from parse import Parse
from threading import Thread
#############
import threading

rec = Receive()
par = Parse()

def start_receive():
    if not rec.getRunning() and not par.getRunning():
        input1 = receive_input1.get()
        input2 = receive_input2.get()
        input3 = receive_input3.get()
        Thread(target=rec.main, args=(input1, input2, input3), daemon=True).start()


def stop_receive():
    # Only runs if receive is running
    if rec.getRunning():
        print (str(rec.getRunning()))
        rec.toggleStop()
        print ("\nStopped running")

def log_zv():
    if rec.getRunning():
        rec.toggleZV()
        print ("\nLogged Zero-velocity")

def run_parse():
    if not rec.getRunning() and not par.getRunning():
        input1 = receive_input1.get()
        input2 = receive_input2.get()
        input3 = receive_input3.get()
        Thread(target=par.plot_data, args=(input1, input2, input3), daemon=True).start()

# Create the main window
window = Tk()
window.geometry('800x500')
window.title("Simple GUI")
window.configure(padx=20, pady=20)

# Receive section
Label(window, text="Enter trial type (Default: hallway):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
receive_input1 = Entry(window, width=50)
receive_input1.grid(row=1, column=1, padx=5, pady=5)

Label(window, text="Enter trial speed (Default: walk):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
receive_input2 = Entry(window, width=50)
receive_input2.grid(row=2, column=1, padx=5, pady=5)

Label(window, text="Enter CSV file name (Default: exportfile):").grid(row=3, column=0, sticky='w', padx=5, pady=5)
receive_input3 = Entry(window, width=50)
receive_input3.grid(row=3, column=1, padx=5, pady=5)

receive_button1 = Button(window, text="Start Receive", command=start_receive)
receive_button1.grid(row=4, column=0, columnspan=2, pady=5)

receive_button2 = Button(window, text="Stop Receive", command=stop_receive)
receive_button2.grid(row=5, column=0, columnspan=2, pady=5)

log_stationary = Button(window, text="Log Zero-Velocity", command=log_zv)
log_stationary.grid(row=6, column=0, columnspan=2, pady=5)

# Parse section
Label(window, text="Enter trial type (Default: hallway):").grid(row=7, column=0, sticky='w', padx=5, pady=5)
parse_input1 = Entry(window, width=50)
parse_input1.grid(row=7, column=1, padx=5, pady=5)

Label(window, text="Enter trial speed (Default: walk):").grid(row=8, column=0, sticky='w', padx=5, pady=5)
parse_input2 = Entry(window, width=50)
parse_input2.grid(row=8, column=1, padx=5, pady=5)

Label(window, text="Enter CSV file name (Default: exportfile):").grid(row=9, column=0, sticky='w', padx=5, pady=5)
parse_input3 = Entry(window, width=50)
parse_input3.grid(row=9, column=1, padx=5, pady=5)

parse_button = Button(window, text="Parse", command=run_parse)
parse_button.grid(row=10, column=0, columnspan=2, pady=5)

#########################

def active_count():
    print (threading.active_count())

def enum_threads():
    for thread in threading.enumerate(): 
        print(thread.name)

debug_button1 = Button(window, text="DEBUG count threads", command=active_count)
debug_button1.grid(row=11, column=0, columnspan=1, pady=1)

debug_button2 = Button(window, text="DEBUG enum threads", command=enum_threads)
debug_button2.grid(row=11, column=1, columnspan=1, pady=1)

# Run the window
window.mainloop()
