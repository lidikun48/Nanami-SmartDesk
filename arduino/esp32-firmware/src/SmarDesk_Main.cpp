/*
  SmartDeskHub ESP32 – v3.0 HARDWARE FIX
  Role: Nervous System
  Author: Chiko x Nanami
  
  LOGIC REVISION:
  - FAN (Relay Laptop): Active LOW (Standard Module). Auto by Presence.
  - LAMP (Relay Maintenance): Active HIGH (Request User). Manual Only.
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <NewPing.h>
#include <DHT.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>

// ... (NETWORK & IP SAMA KAYA SEBELUMNYA) ...
const char* ssid = "YOUR_SSID";
const char* pass = "YOUR_PASSWORD_WIFI";
const char* mqtt_server = "192.168.1.X"; //Sesuaikan IP Raspi
IPAddress local_IP(192, 168, 1, 200); 
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress primaryDNS(8, 8, 8, 8);

// PIN
#define PIN_FAN     26
#define PIN_PI      27 
#define PIN_LAMP    19
#define PIN_TRIG    21
#define PIN_ECHO    22
#define PIN_BUZZER  13
#define PIN_MQ      34
#define PIN_DHT     4

// TOPIC
#define TOPIC_DATA      "smartdesk/sensor/data"
#define TOPIC_STATE     "smartdesk/system/state"
#define TOPIC_CMD       "smartdesk/system/command"
#define TOPIC_CTRL_FAN  "smartdesk/control/fan"
#define TOPIC_CTRL_LAMP "smartdesk/control/lamp"
#define TOPIC_CTRL_BUZZ "smartdesk/control/buzzer"

WiFiClient espClient;
PubSubClient mqtt(espClient);
NewPing sonar(PIN_TRIG, PIN_ECHO, 200);
DHT dht(PIN_DHT, DHT11);

unsigned long lastSensorSend = 0;
bool piPower = true;
bool userPresent = false;
unsigned long awayTimerStart = 0;

void beep(int n, int d=80){
  for(int i=0;i<n;i++){
    digitalWrite(PIN_BUZZER, HIGH); delay(d);
    digitalWrite(PIN_BUZZER, LOW); delay(d);
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int len){
  String msg;
  for(uint8_t i=0;i<len;i++) msg += (char)payload[i];
  String t = String(topic);

  // BUZZER & SYSTEM CMD (Sama)
  if(t == TOPIC_CTRL_BUZZ){
    int count = msg.toInt();
    if(count > 0) beep(count);
  }
  if(t == TOPIC_STATE && msg == "RPI_READY") beep(2);
  if(t == TOPIC_CMD && msg == "SHUTDOWN"){
      beep(3, 200); delay(2000);  
      piPower = false; digitalWrite(PIN_PI, HIGH);
  }

  // === LOGIKA RELAY (DIPERBAIKI) ===
  
  // 1. FAN (Laptop Cooler) - Active LOW (Standard)
  // "ON" -> LOW (Nyala)
  // "OFF" -> HIGH (Mati)
  if(t == TOPIC_CTRL_FAN){
    beep(1); 
    digitalWrite(PIN_FAN, (msg=="ON")?LOW:HIGH);
  }
  
  // 2. LAMP (Maintenance) - Active HIGH (Request User)
  // "ON" -> HIGH (Nyala)
  // "OFF" -> LOW (Mati)
  if(t == TOPIC_CTRL_LAMP){
    beep(1); 
    digitalWrite(PIN_LAMP, (msg=="ON")?HIGH:LOW);
  }
}

void setup(){
  Serial.begin(115200);
  
  // SETUP PIN STATE AWAL
  pinMode(PIN_FAN, OUTPUT);   digitalWrite(PIN_FAN, HIGH); // Fan Mati (Active LOW -> HIGH)
  pinMode(PIN_LAMP, OUTPUT); digitalWrite(PIN_LAMP, LOW); // Lampu Mati (Active HIGH -> LOW)
  pinMode(PIN_PI, OUTPUT);   digitalWrite(PIN_PI, LOW);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_MQ, INPUT);
  dht.begin();

  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS)) {
    Serial.println("STA Failed to configure");
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  while(WiFi.status()!=WL_CONNECTED) delay(500);

  ArduinoOTA.setHostname("SmartDesk-ESP32");
  ArduinoOTA.begin();

  mqtt.setServer(mqtt_server, 1883);
  mqtt.setCallback(mqttCallback);

  beep(1); 
}

void loop(){
  ArduinoOTA.handle();
  if(!mqtt.connected()){
    if (mqtt.connect("ESP32_Nanami")) mqtt.subscribe("smartdesk/#");
    else delay(5000);
  }
  mqtt.loop();

  if(millis() - lastSensorSend > 500){ 
    lastSensorSend = millis();
    int dist = sonar.ping_cm();
    if(dist == 0) dist = 999; 

    // LOGIKA PRESENCE LOKAL
    if(dist > 0 && dist < 80){
      if(!userPresent){
        userPresent = true;
        awayTimerStart = 0;
        beep(2);
      }
      awayTimerStart = 0;
    }
    else {
      if(userPresent){
        if(awayTimerStart == 0) awayTimerStart = millis();
        if(millis() - awayTimerStart > 5000){
          userPresent = false;
          beep(1, 600);
          awayTimerStart = 0;
        }
      }
    }

    static unsigned long lastMqttPub = 0;
    if(millis() - lastMqttPub > 2000){ 
        lastMqttPub = millis();
        int mq = analogRead(PIN_MQ);
        float t = dht.readTemperature();
        if(isnan(t)) t = -999.0;
        char json[128];
        snprintf(json,sizeof(json), "{\"dist\":%d,\"gas\":%d,\"temp\":%.1f}", dist, mq, t);
        mqtt.publish(TOPIC_DATA,json);
    }
  }
}
