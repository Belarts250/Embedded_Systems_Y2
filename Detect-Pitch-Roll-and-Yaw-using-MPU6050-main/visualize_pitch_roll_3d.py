import serial
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

PORT = 'COM6'
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) != 3:
            return None, None
        pitch = float(parts[0])
        roll  = float(parts[1])
        return pitch, roll
    except:
        return None, None

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([-2, 2])
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Pitch and Roll 3D")

while True:
    raw = ser.readline().decode(errors="ignore")
    pitch, roll = parse_line(raw)
    if pitch is not None:
        # Map pitch and roll to a vector (ignoring yaw)
        ax.cla()
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        ax.set_zlim([-2, 2])
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("Pitch and Roll 3D")
        
        # Draw simple vector
        ax.quiver(0, 0, 0, np.sin(np.radians(roll)), np.sin(np.radians(pitch)), 0, length=1, color='blue')
        plt.pause(0.01)