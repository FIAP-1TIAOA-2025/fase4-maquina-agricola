#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <Arduino.h>

// Definições de pinos
#define PIN_SENSOR_FOSFORO 19
#define PIN_SENSOR_POTASSIO 18
#define PIN_SENSOR_ANALOGICO_1 32
#define PIN_SENSOR_ANALOGICO_2 33
#define PIN_LDR 34
#define PIN_DHT 35
#define PIN_RELE 5

#define DHTTYPE DHT22

DHT dht(PIN_DHT, DHTTYPE);

void setup() {
  Serial.begin(115200);

  pinMode(PIN_SENSOR_FOSFORO, INPUT_PULLUP);
  pinMode(PIN_SENSOR_POTASSIO, INPUT_PULLUP);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, LOW); // Relé desligado inicialmente

  dht.begin();
}

float simularPH(int valorLDR) {
  // Considerando que valorLDR varia de 0 (muita luz) a 4095 (pouca luz)
  // Vamos mapear para um pH entre 4.0 e 9.0 (faixa comum em solos)
  float phMin = 4.0;
  float phMax = 9.0;
  return phMin + ((phMax - phMin) * (4095 - valorLDR) / 4095.0);
}

void loop() {
  // Leitura dos botões (LOW = pressionado)
  bool fosforoPressionado = digitalRead(PIN_SENSOR_FOSFORO) == LOW; // Se o botão de fósforo estiver pressionado, o solo tem a quantidade desejada  
  bool potassioPressionado = digitalRead(PIN_SENSOR_POTASSIO) == LOW; // Se o botão de potássio estiver pressionado, o solo tem a quantidade desejada

  // Leitura do sensor DHT22
  float umidade = dht.readHumidity();

  // Leitura do sensor LDR (fotoresistor)
  int valorLDR = analogRead(PIN_LDR);

  // Simulação do valor de pH baseado no LDR
  float valorpH = simularPH(valorLDR);

  // Leitura dos sensores analógicos
  int valorSensor1 = analogRead(PIN_SENSOR_ANALOGICO_1);
  int valorSensor2 = analogRead(PIN_SENSOR_ANALOGICO_2);

  // Lógica de acionamento do relé
  bool ligarRele = false;

  // Exemplo: liga o relé se algum botão for pressionado, umidade < 40% ou pouca luz (LDR < 2000)
  if (fosforoPressionado || potassioPressionado || (umidade < 40 && !isnan(umidade)) || ( valorpH < 9 && valorpH > 4 )) {
    ligarRele = true;
  }

  digitalWrite(PIN_RELE, ligarRele ? HIGH : LOW);

  // Debug
  Serial.print("Fósforo: "); Serial.print(fosforoPressionado);
  Serial.print(" | Potássio: "); Serial.print(potassioPressionado);
  Serial.print(" | Umidade: "); Serial.print(umidade);
  Serial.print(" | pH (sim): "); Serial.print(valorpH);
  Serial.print(" | Sensor1: "); Serial.print(valorSensor1);
  Serial.print(" | Sensor2: "); Serial.print(valorSensor2);
  Serial.print(" | Relé: "); Serial.println(ligarRele ? "LIGADO" : "DESLIGADO");

  delay(1000);
}