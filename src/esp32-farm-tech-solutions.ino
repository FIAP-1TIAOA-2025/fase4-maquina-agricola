#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHTesp.h>
#include <Arduino.h>
#include <LiquidCrystal_I2C.h>

// I2C LCD address must be defined before use
#define LCD_ADDR           0x27
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);  // 16×2 LCD over I²C :contentReference[oaicite:4]{index=4}

// Pin definitions
#define PIN_SENSOR_FOSFORO 19
#define PIN_SENSOR_POTASSIO 18
#define PIN_LDR            34
#define PIN_DHT            15
#define PIN_RELE           5

#define DHTTYPE DHT22

DHTesp dht;
bool sensorFosforo = false;
bool sensorPotassio = false;

// Simulate pH from LDR reading
float simularPH(int valorLDR) {
  float phMin = 4.0;
  float phMax = 9.0;
  return phMin + ((phMax - phMin) * (4095 - valorLDR) / 4095.0);
}

void setup() {
  Serial.begin(115200);

  // Inicializa butoes e sensores
  pinMode(PIN_SENSOR_FOSFORO, INPUT_PULLUP);
  pinMode(PIN_SENSOR_POTASSIO, INPUT_PULLUP);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW);  // Relay desligado inicialmente

  // inicializa DHT sensor :contentReference[oaicite:5]{index=5}
  dht.setup(PIN_DHT, DHTesp::DHT22);

  // Initialize the I2C LCD :contentReference[oaicite:6]{index=6}
  Wire.begin(21, 22);      // SDA = GPIO21, SCL = GPIO22
  lcd.init();              // Initialize LCD
  lcd.backlight();         // Turn on backlight
}

void loop() {
  // Toggle phosphorus sensor state on button press
  if (digitalRead(PIN_SENSOR_FOSFORO) == LOW) {
    sensorFosforo = !sensorFosforo;
    Serial.print("Fósforo: "); Serial.println(sensorFosforo);
    delay(500);  // debounce
  }
  // Toggle potassium sensor state on button press
  if (digitalRead(PIN_SENSOR_POTASSIO) == LOW) {
    sensorPotassio = !sensorPotassio;
    Serial.print("Potássio: "); Serial.println(sensorPotassio);
    delay(500);  // debounce
  }

  // Read humidity from DHT22
  TempAndHumidity data = dht.getTempAndHumidity();
  float umidade = data.humidity;

  // Read LDR and simulate pH
  int valorLDR = analogRead(PIN_LDR);
  float valorpH = simularPH(valorLDR);

  // Irrigation logic
  bool ligarRele = (sensorFosforo && sensorPotassio &&
                    umidade < 40.0 &&
                    valorpH > 5.5 && valorpH < 6.5);

  digitalWrite(PIN_RELE, ligarRele ? HIGH : LOW);

  // Serial debug for Plotter 
  Serial.print("Fósforo: ");    Serial.print(sensorFosforo);
  Serial.print(" | Potássio: ");Serial.print(sensorPotassio);
  Serial.print(" | Umidade: ");  Serial.print(umidade);
  Serial.print(" | pH (sim): "); Serial.print(valorpH);
  Serial.print(" | Relé: ");     Serial.println(ligarRele ? "LIGADO" : "DESLIGADO");

  // Update LCD display :contentReference[oaicite:8]{index=8}
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("U:"); lcd.print(umidade, 1);
  lcd.print("% pH:"); lcd.print(valorpH, 1);
  lcd.setCursor(0, 1);
  lcd.print("P:Sf "); lcd.print(sensorFosforo ? "1" : "0");
  lcd.print(" K:"); lcd.print(sensorPotassio ? "1" : "0");
  lcd.print(" R:"); lcd.print(ligarRele ? "1" : "0");

  delay(1000);
}
