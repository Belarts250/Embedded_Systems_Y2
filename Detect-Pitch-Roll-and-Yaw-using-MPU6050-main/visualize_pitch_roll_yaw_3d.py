import sys
import math
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Patch

PORT = 'COM6'
BAUD = 115200
WINDOW = 200
ser = serial.Serial(PORT, BAUD, timeout=1)

pitch_buf = deque(maxlen=WINDOW)
roll_buf  = deque(maxlen=WINDOW)
yaw_buf   = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

fig = plt.figure(figsize=(9, 7))
ax1 = fig.add_subplot(2,1,1)
(line_pitch,) = ax1.plot([], [], label="Pitch (°)")
(line_roll,)  = ax1.plot([], [], label="Roll (°)")
(line_yaw,)   = ax1.plot([], [], label="Yaw (°)")
ax1.set_xlim(0, WINDOW)
ax1.set_ylim(-180, 180)
ax1.set_xlabel("Samples")
ax1.set_ylabel("Angle (°)")
ax1.set_title("MPU6050 Pitch, Roll & Yaw")
ax1.legend(loc="upper right")

ax2 = fig.add_subplot(2,1,2, projection="3d")
ax2.set_xlim([-2, 2])
ax2.set_ylim([-2, 2])
ax2.set_zlim([-2, 2])
ax2.set_title("3D Orientation")
ax2.set_box_aspect([1,1,1])

cube_definition = [np.array(v) for v in [(-1, -1, -1), (-1, -1,  1), (-1,  1, -1),
                                         (-1,  1,  1), (1, -1, -1), (1, -1,  1),
                                         (1,  1, -1), (1,  1,  1)]]

faces = [
    [cube_definition[0], cube_definition[1], cube_definition[3], cube_definition[2]],
    [cube_definition[4], cube_definition[5], cube_definition[7], cube_definition[6]],
    [cube_definition[0], cube_definition[1], cube_definition[5], cube_definition[4]],
    [cube_definition[2], cube_definition[3], cube_definition[7], cube_definition[6]],
    [cube_definition[1], cube_definition[3], cube_definition[7], cube_definition[5]],
    [cube_definition[0], cube_definition[2], cube_definition[6], cube_definition[4]],
]

face_colors = ["red","green","blue","yellow","orange","cyan"]
cube_collection = Poly3DCollection(faces, facecolors=face_colors, linewidths=1, edgecolors="black", alpha=0.7)
ax2.add_collection3d(cube_collection)

def rotation_matrix(pitch, roll, yaw):
    pitch = math.radians(pitch)
    roll  = math.radians(roll)
    yaw   = math.radians(yaw)
    Rx = np.array([[1,0,0],[0,math.cos(roll),-math.sin(roll)],[0,math.sin(roll),math.cos(roll)]])
    Ry = np.array([[math.cos(pitch),0,math.sin(pitch)],[0,1,0],[-math.sin(pitch),0,math.cos(pitch)]])
    Rz = np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1]])
    return Rz @ Ry @ Rx

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) != 3: return None, None, None
        return float(parts[0]), float(parts[1]), float(parts[2])
    except: return None, None, None

def init():
    line_pitch.set_data([], [])
    line_roll.set_data([], [])
    line_yaw.set_data([], [])
    return (line_pitch, line_roll, line_yaw, cube_collection)

def update(frame):
    for _ in range(5):
        raw = ser.readline().decode(errors="ignore")
        if not raw: break
        pitch, roll, yaw = parse_line(raw)
        if pitch is None: continue
        pitch_buf.append(pitch)
        roll_buf.append(roll)
        yaw_buf.append(yaw)
        x_idx.append(len(x_idx) + 1 if x_idx else 1)
    
    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    line_roll.set_data(xs, list(roll_buf))
    line_yaw.set_data(xs, list(yaw_buf))
    ax1.set_xlim(max(0, len(xs)-WINDOW), max(WINDOW, len(xs)))
    
    if pitch_buf and roll_buf and yaw_buf:
        R = rotation_matrix(pitch_buf[-1], roll_buf[-1], yaw_buf[-1])
        rotated_vertices = [R @ v for v in cube_definition]
        new_faces = [
            [rotated_vertices[0], rotated_vertices[1], rotated_vertices[3], rotated_vertices[2]],
            [rotated_vertices[4], rotated_vertices[5], rotated_vertices[7], rotated_vertices[6]],
            [rotated_vertices[0], rotated_vertices[1], rotated_vertices[5], rotated_vertices[4]],
            [rotated_vertices[2], rotated_vertices[3], rotated_vertices[7], rotated_vertices[6]],
            [rotated_vertices[1], rotated_vertices[3], rotated_vertices[7], rotated_vertices[5]],
            [rotated_vertices[0], rotated_vertices[2], rotated_vertices[6], rotated_vertices[4]],
        ]
        cube_collection.set_verts(new_faces)
    return (line_pitch, line_roll, line_yaw, cube_collection)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False)
plt.tight_layout()
plt.show()