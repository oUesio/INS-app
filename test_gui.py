from tkinter import *
import receive
import parse
from threading import Thread
import tools
#############
import threading

rec = receive.Receive()
par = parse.Parse()

def start_receive():
    # Only runs if receive is not running
    if not rec.getRunning():
        Thread(target=rec.main, args=(receive_input1.get(),receive_input2.get(),)).start()

def stop_receive():
    # Only runs if receive is running
    if rec.getRunning():
        rec.toggleStop()
        print ("\nStopped running")

def run_parse():
    if not par.getRunning():
        par.main(parse_input1.get(), parse_input2.get())

# Create the main window
window = Tk()
window.geometry('600x400')
window.title("Simple GUI")

label1 = Label(window, text="Enter mtb file name (Default: logfile):")
label1.pack()

receive_input1 = Entry(window, width=50)
receive_input1.pack()

label2 = Label(window, text="Enter csv file name (Default: exportfile):")
label2.pack()

receive_input2 = Entry(window, width=50)
receive_input2.pack()

receive_button1 = Button(window, text="Start Receive", command=start_receive)
receive_button1.pack()

receive_button2 = Button(window, text="Stop Receive", command=stop_receive)
receive_button2.pack()


label3 = Label(window, text="Enter mtb file name (Default: logfile):")
label3.pack()

parse_input1 = Entry(window, width=50)
parse_input1.pack()

label4 = Label(window, text="Enter csv file name (Default: exportfileTEMP):")
label4.pack()

parse_input2 = Entry(window, width=50)
parse_input2.pack()

parse_button = Button(window, text="Parse", command=run_parse)
parse_button.pack()

parse_csv_button = Button(window, text="Parse CSV", command=lambda: tools.parse_csv())
parse_csv_button.pack()

#########################

def active_count():
    print (threading.active_count())

def enum_threads():
    for thread in threading.enumerate(): 
        print(thread.name)

debug_button1 = Button(window, text="DEBUG count threads", command=active_count)
debug_button1.pack()

debug_button2 = Button(window, text="DEBUG enum threads", command=enum_threads)
debug_button2.pack()

# Start the Tkinter main loop
window.mainloop()
