// ---------------- BLYNK ----------------
#define BLYNK_TEMPLATE_ID "TMPL3DLeIFiZ9"
#define BLYNK_TEMPLATE_NAME "Smart Irrigation"
#define BLYNK_AUTH_TOKEN "hA48yP2em6le0QhNRb8aW34OG2scL1WB"

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>

// ---------------- WIFI ----------------
char ssid[] = "nazeem07";
char pass[] = "Nazeem007";

// ---------------- OLED + SENSORS ----------------
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <DHT.h>
#include <ESP32Servo.h>

#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34
#define SERVO_PIN 18

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
DHT dht(DHTPIN, DHTTYPE);
Servo servo;

BlynkTimer timer;

// ------------ SEND DATA TO BLYNK ------------
void sendToBlynk() {
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();

  int soilValue = analogRead(SOIL_PIN);
  int soilPercent = map(soilValue, 0, 4095, 100, 0);

  String gateStatus;

  // ---- SERVO CONTROL ----
  if (soilPercent < 30) {
    servo.write(90);     // OPEN
    gateStatus = "OPEN";
  } else {
    servo.write(0);      // CLOSED
    gateStatus = "CLOSED";
  }

  // ---- SEND TO BLYNK ----
  Blynk.virtualWrite(V0, soilPercent);
  Blynk.virtualWrite(V1, temp);
  Blynk.virtualWrite(V2, humidity);
  Blynk.virtualWrite(V3, gateStatus);
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);

  // Start WiFi + Blynk
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);

  dht.begin();
  pinMode(SOIL_PIN, INPUT);

  servo.attach(SERVO_PIN);
  servo.write(0);

  Wire.begin(21, 22);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found!");
    while (1);
  }
  display.clearDisplay();
  display.display();

  timer.setInterval(1500, sendToBlynk);
}

// ---------------- LOOP ----------------
void loop() {
  Blynk.run();
  timer.run();

  // -------- OLED DISPLAY --------
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();

  int soilValue = analogRead(SOIL_PIN);
  int soilPercent = map(soilValue, 0, 4095, 100, 0);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.setCursor(0, 0);
  display.print("Temp: ");
  display.print(temp);
  display.println(" C");

  display.setCursor(0, 12);
  display.print("Humidity: ");
  display.print(humidity);
  display.println(" %");

  display.setCursor(0, 24);
  display.print("Soil: ");
  display.print(soilPercent);
  display.println(" %");

  display.display();
}