
#include <SoftwareSerial.h>

#define BT_RX 10  
#define BT_TX 11 

SoftwareSerial BT(BT_RX, BT_TX); // RX, TX

void setup() {
  Serial.begin(38400);    
  BT.begin(38400);       
  Serial.println("🚀 Bluetooth bridge online...");
}

void loop() {
  // ➡️ PC → Bluetooth
  if (Serial.available()) {
    char c = Serial.read();
    BT.write(c);
  }

  // ⬅️ Bluetooth → PC
  if (BT.available()) {
    String msg = BT.readStringUntil('\n');
    Serial.println(" BT → " + msg);
  }
}
