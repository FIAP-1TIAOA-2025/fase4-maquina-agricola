#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHTesp.h>
#include <Arduino.h>

// Definições de pinos
#define PIN_SENSOR_FOSFORO 19
#define PIN_SENSOR_POTASSIO 18
#define PIN_LDR 34
#define PIN_DHT 15
#define PIN_RELE 5

#define DHTTYPE DHT22

DHTesp dht;

void setup() {
  Serial.begin(115200);

  pinMode(PIN_SENSOR_FOSFORO, INPUT_PULLUP);
  pinMode(PIN_SENSOR_POTASSIO, INPUT_PULLUP);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW); // Relé desligado inicialmente

  dht.setup(PIN_DHT, DHTesp::DHT22);
}

float simularPH(int valorLDR) {
  // Considerando que valorLDR varia de 0 (muita luz) a 4095 (pouca luz)
  // Vamos mapear para um pH entre 4.0 e 9.0 (faixa comum em solos)
  float phMin = 4;
  float phMax = 9;
  return phMin + ((phMax - phMin) * (4095 - valorLDR) / 4095.0);
}

bool sensorFosforo = false;
bool sensorPotassio = false;

void loop() {
  // Leitura dos botões (LOW = pressionado)
  if(digitalRead(PIN_SENSOR_FOSFORO) == LOW){
    sensorFosforo = !sensorFosforo; // Alternar entre quantidades de fosforo boas e ruins
    Serial.print("****************************************: ");
    Serial.print("Fósforo: "); Serial.print(sensorFosforo);
    Serial.print("****************************************: ");
    delay(500); // Debounce
  }
  if(digitalRead(PIN_SENSOR_POTASSIO) == LOW){
  sensorPotassio = !sensorPotassio; // Alternar entre quantidades de potassio boas e ruins
  Serial.print("****************************************: ");
  Serial.print("Potassio: "); Serial.print(sensorFosforo);
  Serial.print("****************************************: ");
  delay(500); // Debounce
  }

  // Leitura do sensor DHT22
  TempAndHumidity data = dht.getTempAndHumidity();
  float umidade = data.humidity;

  // Leitura do sensor LDR (fotoresistor)
  int valorLDR = analogRead(PIN_LDR);
  // Simulação do valor de pH baseado no LDR
  float valorpH = simularPH(valorLDR);

  // Lógica de acionamento do relé
  bool ligarRele = false;

  // Exemplo: liga o relé se algum botão for pressionado, umidade < 40% ou pouca luz (LDR < 2000)
  if (sensorFosforo && sensorPotassio && umidade < 40 && ( valorpH < 6.5 && valorpH > 5.5 )) {
    ligarRele = true;
  }

  digitalWrite(PIN_RELE, ligarRele ? HIGH : LOW);

  // Debug
  Serial.print("Fósforo: "); Serial.print(sensorFosforo);
  Serial.print(" | Potássio: "); Serial.print(sensorPotassio);
  Serial.print(" | Umidade: "); Serial.print(umidade);
  Serial.print(" | pH (sim): "); Serial.print(valorpH);
  Serial.print(" | Relé: "); Serial.println(ligarRele ? "LIGADO" : "DESLIGADO");

  delay(1000);
}