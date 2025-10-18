import serial
import matplotlib.pyplot as plt
from collections import deque

PORT = 'COM6'  # change if needed
BAUD = 115200
WINDOW = 200

ser = serial.Serial(PORT, BAUD, timeout=1)
pitch_buf = deque(maxlen=WINDOW)
x_idx = deque(maxlen=WINDOW)

plt.ion()
fig, ax = plt.subplots()
line_pitch, = ax.plot([], [], label="Pitch (°)")
ax.set_ylim(-180, 180)
ax.set_xlim(0, WINDOW)
ax.set_xlabel("Samples")
ax.set_ylabel("Pitch (°)")
ax.set_title("MPU6050 Pitch")
ax.legend()

def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) != 3:
            return None
        return float(parts[0])  # pitch
    except:
        return None

while True:
    raw = ser.readline().decode(errors="ignore")
    pitch = parse_line(raw)
    if pitch is not None:
        pitch_buf.append(pitch)
        x_idx.append(len(x_idx) + 1 if x_idx else 1)
        line_pitch.set_data(range(len(pitch_buf)), list(pitch_buf))
        ax.set_xlim(max(0, len(x_idx)-WINDOW), max(WINDOW, len(x_idx)))
        plt.pause(0.01);