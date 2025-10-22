"""
real_game_3d.py
- Connects to Arduino/BT device sending joystick data like {"x":512,"y":512}
- Renders a simple 3D cube and camera that follows/rotates based on joystick
- Uses pygame for display and pyserial to read from Bluetooth serial

Install requirements:
  pip install pygame pyserial

To find your Bluetooth COM port on Windows:
  1. Pair your HC-05/HC-06 Bluetooth module in Windows settings
  2. Check "Bluetooth & devices" -> "Devices" -> Click your HC-05
  3. Look for "COM port" (e.g., COM5)
  4. Set SERIAL_PORT below to that port, or leave as None for auto-detect
"""

import pygame, sys, math, time, threading, queue, json
from pygame.math import Vector3, Vector2

# ---------- Configuration ----------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# IMPORTANT: Set this to your Bluetooth COM port!
# Windows: "COM5", "COM7", etc. (check Device Manager)
# Linux: "/dev/rfcomm0" or "/dev/ttyUSB0"
# Mac: "/dev/cu.HC-05-DevB" or similar
# Can also be set via BT_COM_PORT environment variable (used by auto-launcher)
SERIAL_PORT = os.environ.get('BT_COM_PORT', None)  # None for auto-detect, or specify: "COM5"
SERIAL_BAUD = 9600

# Joystick mapping
ANALOG_MIN, ANALOG_MAX = 0, 1023
DEADZONE = 60  # center deadzone

# Movement speeds
FORWARD_SPEED = 220.0   # units per second
ROT_SPEED = 160.0       # degrees per second
SENSITIVITY_ROT = 0.25  # joystick X->rotation multiplier
SENSITIVITY_MOVE = 0.6  # joystick Y->forward multiplier

# 3D projection
FOV = 90.0
NEAR_PLANE = 0.1
FAR_PLANE = 1000.0

# ---------- Serial Setup ----------
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except Exception:
    SERIAL_AVAILABLE = False
    print("WARNING: pyserial not installed. Install with: pip install pyserial")

def find_serial_port():
    """Auto-detect Bluetooth/Arduino serial port if SERIAL_PORT is None."""
    if SERIAL_PORT:
        print(f"Using configured port: {SERIAL_PORT}")
        return SERIAL_PORT
    
    if not SERIAL_AVAILABLE:
        return None
    
    ports = list(serial.tools.list_ports.comports())
    print("\n=== Available Serial Ports ===")
    
    for i, p in enumerate(ports):
        print(f"{i+1}. {p.device} - {p.description}")
        # Look for Bluetooth or Arduino keywords
        name = (p.device + " " + (p.description or "")).lower()
        if "bluetooth" in name or "hc-05" in name or "hc-06" in name:
            print(f"   -> Detected Bluetooth device, using {p.device}")
            return p.device
    
    # Fallback to first port
    if ports:
        print(f"No Bluetooth device detected, using first port: {ports[0].device}")
        return ports[0].device
    
    print("No serial ports found!")
    return None

class SerialReader(threading.Thread):
    """Background thread to read serial data from Bluetooth."""
    def __init__(self, port, baud, out_q):
        super().__init__(daemon=True)
        self.out_q = out_q
        self.port = port
        self.baud = baud
        self.running = True
        self.ser = None
        self.connected = False

    def run(self):
        if not SERIAL_AVAILABLE or not self.port:
            return
        
        print(f"\nAttempting to connect to {self.port}...")
        
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            self.connected = True
            print(f"✓ Connected to {self.port} at {self.baud} baud")
            print("Waiting for joystick data...\n")
        except Exception as e:
            print(f"✗ Serial connection failed: {e}")
            print("Check that:")
            print("  1. Bluetooth device is paired")
            print("  2. Correct COM port is set")
            print("  3. No other program is using the port")
            return
        
        buffer = ""
        while self.running:
            try:
                chunk = self.ser.read(256)
                if not chunk:
                    continue
                
                try:
                    text = chunk.decode('utf-8', errors='ignore')
                except Exception:
                    text = str(chunk)
                
                buffer += text
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse JSON joystick data
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict) and 'x' in obj and 'y' in obj:
                            self.out_q.put(('joy', int(obj['x']), int(obj['y'])))
                    except json.JSONDecodeError:
                        # Not JSON, ignore or print for debugging
                        if "===" in line or "Started" in line:
                            print(f"Arduino: {line}")
                        pass
                        
            except Exception as e:
                if self.running:
                    print(f"Serial read error: {e}")
                time.sleep(0.2)
        
        if self.ser:
            self.ser.close()
            print("Serial connection closed")

    def stop(self):
        self.running = False

# ---------- 3D Math ----------
def rotate_point(px, py, pz, yaw_deg, pitch_deg=0, roll_deg=0):
    """Rotate point by yaw, pitch, roll (degrees) around origin."""
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)

    # Yaw (around Y)
    x1 = px * math.cos(yaw) - pz * math.sin(yaw)
    z1 = px * math.sin(yaw) + pz * math.cos(yaw)
    y1 = py

    # Pitch (around X)
    y2 = y1 * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y1 * math.sin(pitch) + z1 * math.cos(pitch)
    x2 = x1

    # Roll (around Z)
    x3 = x2 * math.cos(roll) - y2 * math.sin(roll)
    y3 = x2 * math.sin(roll) + y2 * math.cos(roll)
    z3 = z2

    return x3, y3, z3

def project_point(px, py, pz, cam_pos, cam_yaw, screen_w, screen_h):
    """Transform world coordinates to screen coordinates."""
    # Translate relative to camera
    rx = px - cam_pos[0]
    ry = py - cam_pos[1]
    rz = pz - cam_pos[2]
    
    # Rotate by -cam_yaw
    x_cam, y_cam, z_cam = rotate_point(rx, ry, rz, -cam_yaw, 0, 0)
    
    # Perspective projection
    if z_cam <= 0.01:  # behind camera
        return None
    
    f = (screen_w / 2) / math.tan(math.radians(FOV / 2))
    screen_x = (x_cam * f) / z_cam + screen_w / 2
    screen_y = (-y_cam * f) / z_cam + screen_h / 2
    return (int(screen_x), int(screen_y), z_cam)

# ---------- Cube Geometry ----------
CUBE_VERTS = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
]

CUBE_FACES = [
    (0,1,2,3), (4,5,6,7), (0,1,5,4),
    (2,3,7,6), (1,2,6,5), (0,3,7,4),
]

FACE_COLORS = [
    (150,150,160), (180,160,130), (120,170,190),
    (200,140,140), (160,200,140), (160,140,200)
]

# ---------- Main Game ----------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Real Game 3D - Bluetooth Joystick Control")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.font_big = pygame.font.SysFont("Consolas", 24, bold=True)

        # Camera and player
        self.cam_pos = [0.0, 0.0, -6.0]
        self.cam_yaw = 0.0
        self.player_pos = [0.0, 0.0, 0.0]
        self.player_yaw = 0.0

        # Cube
        self.cube_pos = [0.0, 0.0, 8.0]
        self.cube_scale = 2.2
        self.cube_angle = 0.0

        # Input state
        self.forward = 0.0
        self.turn = 0.0
        self.last_joy_x = 512
        self.last_joy_y = 512

        # Serial setup
        self.q = queue.Queue()
        self.serial_thread = None
        self.serial_port = find_serial_port()
        self.bt_connected = False
        
        if self.serial_port and SERIAL_AVAILABLE:
            self.serial_thread = SerialReader(self.serial_port, SERIAL_BAUD, self.q)
            self.serial_thread.start()
            time.sleep(0.5)  # Give thread time to connect
            self.bt_connected = self.serial_thread.connected
        else:
            print("\n=== KEYBOARD MODE ===")
            print("No Bluetooth connection. Using keyboard controls:")
            print("  W/S - Move forward/backward")
            print("  Q/E - Turn left/right")
            print("  SPACE - Quick dash forward")
            print("  ESC - Quit\n")

    def handle_serial_messages(self):
        """Process queued serial messages (joystick data)."""
        while not self.q.empty():
            msg = self.q.get_nowait()
            if msg[0] == 'joy':
                x_raw, y_raw = msg[1], msg[2]
                self.last_joy_x = x_raw
                self.last_joy_y = y_raw
                
                # Center around midpoint
                x = x_raw - (ANALOG_MAX + ANALOG_MIN) / 2
                y = y_raw - (ANALOG_MAX + ANALOG_MIN) / 2
                
                # Apply deadzone
                if abs(x) < DEADZONE: x = 0
                if abs(y) < DEADZONE: y = 0
                
                # Normalize to -1..1
                x_norm = max(-1.0, min(1.0, x / ((ANALOG_MAX - ANALOG_MIN) / 2)))
                y_norm = max(-1.0, min(1.0, y / ((ANALOG_MAX - ANALOG_MIN) / 2)))
                
                # Map to controls (Y inverted for forward/back)
                self.forward = -y_norm * SENSITIVITY_MOVE
                self.turn = x_norm * SENSITIVITY_ROT
                
                if not self.bt_connected:
                    self.bt_connected = True
                    print("✓ Receiving joystick data!\n")

    def handle_input(self, dt):
        """Handle keyboard input (fallback control)."""
        keys = pygame.key.get_pressed()
        
        # Only use keyboard if no joystick input
        if not (self.forward or self.turn):
            k_forward = 0.0
            if keys[pygame.K_w]: k_forward += 1.0
            if keys[pygame.K_s]: k_forward -= 1.0
            self.forward = k_forward
            
            k_turn = 0.0
            if keys[pygame.K_q]: k_turn += 1.0
            if keys[pygame.K_e]: k_turn -= 1.0
            self.turn = k_turn * (ROT_SPEED / 180.0)
        
        # Event handling
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.key == pygame.K_SPACE:
                    # Dash forward
                    yaw_rad = math.radians(self.player_yaw)
                    self.player_pos[0] += math.sin(yaw_rad) * 2.0
                    self.player_pos[2] += math.cos(yaw_rad) * 2.0

    def update(self, dt):
        """Update game state."""
        self.handle_serial_messages()
        
        # Update player rotation
        self.player_yaw += self.turn * ROT_SPEED * dt
        
        # Move forward in player direction
        if abs(self.forward) > 0.001:
            yaw_rad = math.radians(self.player_yaw)
            dx = math.sin(yaw_rad) * self.forward * FORWARD_SPEED * dt
            dz = math.cos(yaw_rad) * self.forward * FORWARD_SPEED * dt
            self.player_pos[0] += dx
            self.player_pos[2] += dz
        
        # Camera follows player
        cam_distance = 8.0
        cam_height = 2.5
        yaw_rad = math.radians(self.player_yaw)
        self.cam_pos[0] = self.player_pos[0] - math.sin(yaw_rad) * cam_distance
        self.cam_pos[2] = self.player_pos[2] - math.cos(yaw_rad) * cam_distance
        self.cam_pos[1] = self.player_pos[1] + cam_height
        self.cam_yaw = self.player_yaw
        
        # Rotate cube for effect
        self.cube_angle = (time.time() * 25.0) % 360.0

    def draw(self):
        """Render the 3D scene."""
        self.screen.fill((18, 18, 24))
        
        # Draw ground grid
        for gx in range(-50, 51, 2):
            x1, z1 = gx * 1.0, -50.0
            x2, z2 = gx * 1.0, 50.0
            p1 = project_point(x1, 0.0, z1, self.cam_pos, self.cam_yaw, SCREEN_W, SCREEN_H)
            p2 = project_point(x2, 0.0, z2, self.cam_pos, self.cam_yaw, SCREEN_W, SCREEN_H)
            if p1 and p2:
                pygame.draw.aaline(self.screen, (28,28,36), (p1[0],p1[1]), (p2[0],p2[1]))
        
        # Draw cube
        verts_trans = []
        for vx, vy, vz in CUBE_VERTS:
            sx = vx * self.cube_scale
            sy = vy * self.cube_scale
            sz = vz * self.cube_scale
            rx, ry, rz = rotate_point(sx, sy, sz, self.cube_angle, 0, 0)
            wx = rx + self.cube_pos[0]
            wy = ry + self.cube_pos[1]
            wz = rz + self.cube_pos[2]
            verts_trans.append((wx, wy, wz))
        
        # Sort faces by depth
        face_draws = []
        for fi, face in enumerate(CUBE_FACES):
            pts = [project_point(*verts_trans[idx], self.cam_pos, self.cam_yaw, SCREEN_W, SCREEN_H) 
                   for idx in face]
            if any(p is None for p in pts):
                continue
            avg_z = sum(p[2] for p in pts) / len(pts)
            face_draws.append((avg_z, fi, pts))
        
        face_draws.sort(key=lambda x: -x[0])
        
        # Draw faces
        for _, fi, pts in face_draws:
            poly = [(p[0], p[1]) for p in pts]
            color = FACE_COLORS[fi % len(FACE_COLORS)]
            shade = 1.0 - (abs(pts[0][2]) / 50.0)
            shade = max(0.4, min(1.0, shade))
            shaded = tuple(max(0, min(255, int(c * shade))) for c in color)
            pygame.draw.polygon(self.screen, shaded, poly)
            pygame.draw.polygon(self.screen, (0,0,0), poly, 2)
        
        # HUD
        status_color = (100, 255, 100) if self.bt_connected else (255, 100, 100)
        status_text = "Bluetooth Connected" if self.bt_connected else "Keyboard Mode"
        self.screen.blit(self.font_big.render(status_text, True, status_color), (12, 12))
        
        pos_text = f"Pos: ({self.player_pos[0]:.1f}, {self.player_pos[1]:.1f}, {self.player_pos[2]:.1f})  Yaw: {self.player_yaw:.1f}°"
        self.screen.blit(self.font.render(pos_text, True, (230,230,230)), (12, 42))
        
        input_text = f"Forward: {self.forward:.2f}  Turn: {self.turn:.2f}"
        self.screen.blit(self.font.render(input_text, True, (200,200,200)), (12, 66))
        
        if self.bt_connected:
            joy_text = f"Joystick: X={self.last_joy_x}  Y={self.last_joy_y}"
            self.screen.blit(self.font.render(joy_text, True, (150,200,255)), (12, 90))
        
        pygame.display.flip()

    def run(self):
        """Main game loop."""
        self.running = True
        prev = time.time()
        
        while self.running:
            now = time.time()
            dt = now - prev
            prev = now
            dt = max(0.0, min(1/15, dt))
            
            self.handle_input(dt)
            self.update(dt)
            self.draw()
            
            self.clock.tick(FPS)
        
        if self.serial_thread:
            self.serial_thread.stop()
        pygame.quit()

if __name__ == "__main__":
    print("=" * 50)
    print("3D Game with Bluetooth Joystick Control")
    print("=" * 50)
    g = Game()
    g.run()