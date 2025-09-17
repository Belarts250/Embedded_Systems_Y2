import pygame
import serial

pygame.init()

# Window setup
win_width, win_height = 800, 600
win = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption("Joystick Game")

# Character setup
character_size = 50
character_color = (106,13,173)  # Initial color (red)
character_x, character_y = win_width // 2, win_height // 2
character_speed = 5

# Serial communication setup
arduino_port = 'COM5'  # Replace with your Arduino port
ser = serial.Serial(arduino_port, 9600)

running = True

# Store the character's previous position
prev_x, prev_y = character_x, character_y

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    try:
        line = ser.readline().decode().strip()
        if line:  # make sure it's not empty
            data = line.split(',')
            if len(data) == 3 and all(d.isdigit() for d in data):
                joy_x, joy_y, button_state = map(int, data)
                print(f"X: {joy_x}, Y: {joy_y}, Button: {button_state}")

                # Calculate new character position based on joystick input
                new_x = character_x + (joy_x - 512) // 100 * character_speed
                new_y = character_y + (joy_y - 512) // 100 * character_speed

                # Boundaries
                new_x = max(character_size // 2, min(win_width - character_size // 2, new_x))
                new_y = max(character_size // 2, min(win_height - character_size // 2, new_y))

                if (new_x, new_y) != (prev_x, prev_y):
                    character_x, character_y = new_x, new_y

                # Change color on button
                character_color = (0, 0, 255) if button_state == 0 else (255, 0, 0)

    except Exception as e:
        print("Error reading serial:", e)


        # Calculate new character position based on joystick input
        new_x = character_x + (joy_x - 512) // 100 * character_speed
        new_y = character_y + (joy_y - 512) // 100 * character_speed

        # Ensure the character stays within the screen boundaries
        new_x = max(character_size // 2, min(win_width - character_size // 2, new_x))
        new_y = max(character_size // 2, min(win_height - character_size // 2, new_y))

        # Update character position only if it has moved
        if (new_x, new_y) != (prev_x, prev_y):
            character_x, character_y = new_x, new_y

        # Change character color based on buttonState
        character_color = (0, 0, 255) if button_state == 1 else (106,13,173)

    win.fill((255, 255, 255))
    pygame.draw.circle(win, character_color, (character_x, character_y), character_size // 2)
    pygame.display.flip()

# Clean up
ser.close()
pygame.quit()
