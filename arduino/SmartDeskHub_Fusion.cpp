/*
  SmartDeskHub - FUSION ULTIMATE (PATEN)
  Role: Raw Sensor Streamer + Remote Actuator
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <NewPing.h>
#include <DHT.h>

// --- KONFIGURASI JARINGAN ---
const char* ssid        = "TAMPAN & BERANI";
const char* pass        = "Atomic-007";
const char* mqtt_server = "192.168.1.6"; // <--- CEK LAGI IP RASPI LO!

// --- PIN MAPPING ---
#define PIN_FAN     26  // Relay Kipas (Auto via Raspi)
#define PIN_PI      27  // Relay Power Raspi (Active LOW)
#define PIN_LAMP    19  // Relay Lampu (Manual Only)
#define PIN_TRIG    21  // Ultrasonic
#define PIN_ECHO    22
#define PIN_BUZZER  13
#define PIN_MQ      34  // Analog Input
#define PIN_DHT     4   // Digital Input

// --- TOPICS ---
#define TOPIC_DATA     "desk/sensor/data"
#define TOPIC_STATE    "desk/system/state"
#define TOPIC_CMD      "desk/system/command"
#define TOPIC_CTRL_FAN "desk/control/fan"
#define TOPIC_CTRL_LAMP "desk/control/lamp"

NewPing sonar(PIN_TRIG, PIN_ECHO, 200);
DHT dht(PIN_DHT, DHT11);
WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastSensorTime = 0;
bool piPower = true;

// Bunyi Beep Pendek
void beep(int n, int d=80){
  for(int i=0; i<n; i++){
    digitalWrite(PIN_BUZZER, HIGH); delay(d);
    digitalWrite(PIN_BUZZER, LOW); delay(d);
  }
}

// Callback saat ada pesan dari Raspi
void mqttCallback(char* topic, byte* payload, unsigned int len){
  String msg;
  for(uint8_t i=0; i<len; i++) msg += (char)payload[i];
  String t = String(topic);

  // 1. Handshake (Raspi Siap)
  if(t == TOPIC_STATE && msg == "RPI_READY") beep(2);
  
  // 2. Perintah Shutdown (Matikan Relay Raspi)
  if(t == TOPIC_CMD && msg == "SHUTDOWN") {
      beep(3); delay(5000); 
      piPower = false; digitalWrite(PIN_PI, HIGH); 
  }

  // 3. KONTROL RELAY (Dari Raspi)
  if (t == TOPIC_CTRL_FAN) {
      digitalWrite(PIN_FAN, (msg == "ON") ? LOW : HIGH); // Active LOW
  }
  if (t == TOPIC_CTRL_LAMP) {
      digitalWrite(PIN_LAMP, (msg == "ON") ? LOW : HIGH); // Active LOW
  }
}

void setup() {
  Serial.begin(115200);
  
  // Init Relay (PENTING: Nyalakan Raspi Dulu!)
  pinMode(PIN_FAN, OUTPUT); digitalWrite(PIN_FAN, HIGH); // Default OFF
  pinMode(PIN_LAMP, OUTPUT); digitalWrite(PIN_LAMP, HIGH); // Default OFF
  pinMode(PIN_PI, OUTPUT); digitalWrite(PIN_PI, LOW);    // Default ON (Nyalain Raspi)
  
  pinMode(PIN_BUZZER, OUTPUT); 
  pinMode(PIN_MQ, INPUT);
  
  dht.begin();

  // Koneksi WiFi
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  mqtt.setServer(mqtt_server, 1883);
  mqtt.setCallback(mqttCallback);
  beep(1); // Tanda ESP32 Hidup
}

void reconnect() {
  while (!mqtt.connected()) {
    if (mqtt.connect("ESP32_Hybrid")) {
      // Subscribe ke semua channel penting
      mqtt.subscribe(TOPIC_STATE);
      mqtt.subscribe(TOPIC_CMD);
      mqtt.subscribe("desk/control/#"); // Dengerin semua perintah kontrol
    } else {
      delay(2000);
    }
  }
}

void loop() {
  if (!mqtt.connected()) reconnect();
  mqtt.loop();

  // Kirim Data Mentah tiap 1.5 Detik
  if (millis() - lastSensorTime > 1500) {
    lastSensorTime = millis();
    
    int dist = sonar.ping_cm();
    int mq = analogRead(PIN_MQ);
    float t = dht.readTemperature();
    
    // Validasi data
    if (isnan(t)) t = 0;
    if (dist == 0) dist = 999;

    // Format JSON Hemat
    char json[128];
    snprintf(json, sizeof(json), "{\"d\":%d, \"mq\":%d, \"t\":%.1f}", dist, mq, t);
    mqtt.publish(TOPIC_DATA, json);
  }
}