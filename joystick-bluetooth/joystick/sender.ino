
#include <SoftwareSerial.h>

#define BT_RX 10
#define BT_TX 11
#define VRX   A0
#define VRY   A1

SoftwareSerial BT(BT_RX, BT_TX); // RX, TX

void setup() {
  Serial.begin(38400);
  BT.begin(38400);
  Serial.println(" Ready to send joystick data via Bluetooth...");
}

void loop() {
  int x = analogRead(VRX);
  int y = analogRead(VRY);


  Serial.print("X:"); Serial.print(x);
  Serial.print(" | Y:"); Serial.println(y);

  BT.print("X="); BT.print(x);
  BT.print(";Y="); BT.println(y);

  delay(60); 
}
