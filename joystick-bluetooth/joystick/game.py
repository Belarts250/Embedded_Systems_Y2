import pygame, serial, serial.tools.list_ports, time, sys, math

BAUD = 38400

# 🌐 Find Bluetooth Port
def find_bluetooth_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Bluetooth" in p.description or "HC-05" in p.description or "Serial" in p.description:
            print(f"🔗 Connected to {p.device}")
            return serial.Serial(p.device, BAUD, timeout=0.1)
    print("❌ No Bluetooth device found!")
    sys.exit(1)

# 🧱 Cube Colors
FACE_COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255)   # Cyan
]

# 🎮 Cube Control Class
class CubeGame:
    def __init__(self, ser):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption(" Bluetooth Cube Controller")
        self.clock = pygame.time.Clock()
        self.ser = ser

        self.x, self.y = 400, 300
        self.speed = 3

    def read_joystick(self):
        if not self.ser.in_waiting:
            return

        line = self.ser.readline().decode(errors='ignore').strip()
        if "X=" in line and "Y=" in line:
            try:
                parts = line.split(";")
                x_val = int(parts[0].split("=")[1])
                y_val = int(parts[1].split("=")[1])

                # Normalize joystick (0–1023 → -1 to 1)
                nx = (x_val - 512) / 512.0
                ny = (y_val - 512) / 512.0

                # Apply deadzone
                if abs(nx) < 0.1: nx = 0
                if abs(ny) < 0.1: ny = 0

                # Update position
                self.x += nx * self.speed * 10
                self.y += ny * self.speed * 10

            except:
                pass

    def draw_cube(self):
        size = 80
        color = FACE_COLORS[int(time.time() * 2) % len(FACE_COLORS)]
        pygame.draw.rect(self.screen, color, (self.x - size/2, self.y - size/2, size, size))

        # Shadow
        pygame.draw.rect(self.screen, (50, 50, 50), (self.x - size/2 + 10, self.y - size/2 + 10, size, size), 3)

        # Border
        pygame.draw.rect(self.screen, (0, 0, 0), (self.x - size/2, self.y - size/2, size, size), 2)

    def run(self):
        print("🎮 Game Started! Move your joystick to control the cube 💫")

        running = True
        while running:
            self.screen.fill((200, 230, 255))  # light blue sky background

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.read_joystick()
            self.draw_cube()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        self.ser.close()

# 🚀 MAIN
if __name__ == "__main__":
    ser = find_bluetooth_port()
    game = CubeGame(ser)
    game.run()
