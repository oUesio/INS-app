import numpy as np
import csv

def estimate_motion(data, u):
    """
    Estimate distance, orientation, and velocity.
    """

    acc = np.array([data["AccX"], data["AccY"], data["AccZ"]])
    #quaternion = np.array([data["q0"], data["q1"], data["q2"], data["q3"]])
    
    #r = R.from_quat([quaternion[1], quaternion[2], quaternion[3], quaternion[0]])
    #ori = r.as_euler('xyz', degrees=True) 
    time = data['time']
    v = u + acc * time # final velocity to be used for the next group
    d = u * time + (0.5*acc*time**2) # displacement formula using intial velocity, accleration and time
    return ({'distance': d, 'velocity': v})
    #return (dist, vel)#, ori)

def average(subset):
    print ('%s - %s (%s, %s)' % (subset[0]["count"], subset[-1]["count"], subset[0]["timestamp"], subset[-1]["timestamp"]))

    time = (int(subset[-1]["timestamp"]) - int(subset[0]["timestamp"])) / 1000
    avg_acc_x = sum(float(d["AccX"]) for d in subset) / len(subset)
    avg_acc_y = sum(float(d["AccY"]) for d in subset) / len(subset)
    avg_acc_z = sum(float(d["AccZ"]) for d in subset) / len(subset) - 9.80665 # Subtract gravitational acceleration

    return ({"time": time,"AccX": avg_acc_x,"AccY": avg_acc_y,"AccZ": avg_acc_z})

def export_csv(csvfile, keys, data):
    with open(csvfile+'.csv', "w") as outfile:
        dict_writer = csv.DictWriter(outfile, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

def parse_csv(csvfile='exportfile'):
    with open(csvfile+'.csv', mode="r") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader] 

    data_avg = []
    estimates = []
    initial_vel = np.array([0, 0, 0]) # Initial is stationary
    for x in range (len(data) // 20):
        subset = data[x*20: (x*20)+20]
        print (initial_vel)
        avg = average(subset)
        data_avg.append(avg)
        est = estimate_motion(avg, initial_vel)
        initial_vel = est['velocity']
        estimates.append(est)

    if len(data) % 20 != 0:
        last = data[(len(data) // 20)*20:-1]        
        avg = average(last)
        data_avg.append(avg)
        estimates.append(estimate_motion(avg, initial_vel))

    keys1 = data_avg[0].keys()
    export_csv('exportAVERAGE', keys1, data_avg)    
    keys2 = estimates[0].keys()
    export_csv('exportESTIMATES', keys2, estimates)

    print ('Finished parsing the csv file')
