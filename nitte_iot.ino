#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <DHT.h>

// ---------------- PINOUT ----------------
#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34

// ---------- OLED CONFIG ----------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);

  dht.begin();
  pinMode(SOIL_PIN, INPUT);

  // OLED Init
  Wire.begin(21, 22);  // SDA, SCL
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found!");
    for (;;);
  }
  display.clearDisplay();
  display.display();
}

void loop() {
  // -------- READ SENSORS --------
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();

  int soilValue = analogRead(SOIL_PIN);
  int soilPercent = map(soilValue, 0, 4095, 100, 0);  

  // -------- GATE STATUS --------
  String gateStatus;
  if (soilPercent < 30) {
    gateStatus = "OPEN";
  } else {
    gateStatus = "CLOSED";
  }

  // -------- OLED DISPLAY --------
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

  display.setCursor(0, 36);
  display.print("Gate: ");
  display.println(gateStatus);

  display.display();

  // -------- SERIAL MONITOR --------
  Serial.print("Soil: ");
  Serial.print(soilPercent);
  Serial.print("%  Gate: ");
  Serial.println(gateStatus);

  delay(1000);
}
