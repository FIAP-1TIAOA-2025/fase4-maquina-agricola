#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>

// Definições de pinos
#define PIN_SENSOR_FOSFORO 19
#define PIN_SENSOR_POTASSIO 18
#define PIN_DHT 35
#define PIN_RELE 5

#define DHTTYPE DHT22

DHT dht(PIN_DHT, DHTTYPE);
Adafruit_MPU6050 mpu;

void setup() {
  Serial.begin(115200);

  pinMode(PIN_SENSOR_FOSFORO, INPUT_PULLUP);
  pinMode(PIN_SENSOR_POTASSIO, INPUT_PULLUP);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW); // Relé desligado inicialmente

  dht.begin();

  if (!mpu.begin()) {
    Serial.println("Falha ao iniciar MPU6050!");
    while (1);
  }
}

void loop() {
  // Leitura dos botões (LOW = pressionado)
  bool fosforoPressionado = digitalRead(PIN_SENSOR_FOSFORO) == LOW;
  bool potassioPressionado = digitalRead(PIN_SENSOR_POTASSIO) == LOW;

  // Leitura do sensor DHT22
  float umidade = dht.readHumidity();
  float temperatura = dht.readTemperature();

  // Leitura do sensor de pH (simulado via acelerômetro)
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  float ph = a.acceleration.x; // Simulação: use um valor do acelerômetro

  // Lógica de acionamento do relé
  bool ligarRele = false;

  // Exemplo: liga o relé se algum botão for pressionado ou umidade < 40%
  if (fosforoPressionado || potassioPressionado || (umidade < 40 && !isnan(umidade))) {
    ligarRele = true;
  }

  digitalWrite(PIN_RELE, ligarRele ? HIGH : LOW);

  // Debug
  Serial.print("Fósforo: "); Serial.print(fosforoPressionado);
  Serial.print(" | Potássio: "); Serial.print(potassioPressionado);
  Serial.print(" | Umidade: "); Serial.print(umidade);
  Serial.print(" | Temp: "); Serial.print(temperatura);
  Serial.print(" | pH (sim): "); Serial.print(ph);
  Serial.print(" | Relé: "); Serial.println(ligarRele ? "LIGADO" : "DESLIGADO");

  delay(1000);
}