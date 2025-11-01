import serial, serial.tools.list_ports, time

BAUD = 38400
print(" Scanning available COM ports...")

for port in serial.tools.list_ports.comports():
    print(f"🧩 Testing {port.device} ({port.description})")
    try:
        ser = serial.Serial(port.device, BAUD, timeout=1)
        time.sleep(1)
        data = ser.readline().decode(errors='ignore').strip()
        if data:
            print(f"Data received from {port.device}: {data}")
            ser.close()
            break
        ser.close()
    except Exception as e:
        print(f"⚠️ Error on {port.device}: {e}")

print(" Scan complete.")
