import numpy as np
from scipy.spatial.transform import Rotation as R

def estimate_motion(data_array):
    """
    Estimate distance, orientation, and velocity from the given data array.
    
    :param data_array: List of dictionaries containing sensor data.
    :return: A dictionary with estimated distance, velocity, and orientation.
    """
    distance = np.array([0.0, 0.0, 0.0])  # Initial displacement (x, y, z)
    velocity = np.array([0.0, 0.0, 0.0])  # Initial velocity (x, y, z)
    orientations = []  # List to store orientations at each timestep
    timestamps = [entry["timestamp"] for entry in data_array]
    dt = np.diff(timestamps) / 1000  # Convert ms to seconds for time intervals
    
    for i in range(1, len(data_array)):
        acc = np.array([data_array[i]["AccX"], data_array[i]["AccY"], data_array[i]["AccZ"]])
        gyr = np.array([data_array[i]["GyrX"], data_array[i]["GyrY"], data_array[i]["GyrZ"]])
        quaternion = np.array([
            data_array[i]["q0"], data_array[i]["q1"], data_array[i]["q2"], data_array[i]["q3"]
        ])
        
        # Update orientation using quaternion
        r = R.from_quat([quaternion[1], quaternion[2], quaternion[3], quaternion[0]])
        orientations.append(r.as_euler('xyz', degrees=True))  # Store orientation in Euler angles

        # Update velocity using acceleration
        velocity += acc * dt[i - 1]

        # Update displacement using velocity
        distance += velocity * dt[i - 1]
    
    # Return results
    return {
        "distance": distance,
        "velocity": velocity,
        "orientations": orientations
    }

# Example Usage
data_array = [
    {
        "count": 0,
        "timestamp": 0,
        "AccX": 0.0,
        "AccY": 0.0,
        "AccZ": 0.0,
        "GyrX": 0.0,
        "GyrY": 0.0,
        "GyrZ": 0.0,
        "q0": 1.0,
        "q1": 0.0,
        "q2": 0.0,
        "q3": 0.0
    },
    # Add more entries here
]

# Estimate motion
results = estimate_motion(data_array)

# Output results
print("Distance (meters):", results["distance"])
print("Final Velocity (m/s):", results["velocity"])
print("Orientations (Euler angles in degrees):", results["orientations"])
