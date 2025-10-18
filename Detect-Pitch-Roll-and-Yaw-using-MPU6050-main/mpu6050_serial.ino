const int joyXPin = A0;
const int joyYPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT_PULLUP);
}

void loop() {
  int joy_x = analogRead(joyXPin);
  int joy_y = analogRead(joyYPin);
  int buttonState = digitalRead(buttonPin);
  
  Serial.print(joy_x);
  Serial.print(",");
  Serial.print(joy_y);
  Serial.print(",");
  Serial.println(buttonState);
  
  delay(100);
}