# 🤖 Nanami Smart Desk Assistant (v3.0)

**"More than just automation. It's a presence."**

Nanami adalah sistem asisten desktop berbasis **Raspberry Pi Zero 2W** dan **ESP32** yang dirancang untuk memberikan pengalaman "Cinematic" saat bekerja. Sistem ini menggabungkan sensor lingkungan, manajemen daya otomatis (Guardian Mode), dan respons suara dinamis.

---

## 🔥 New Features in v3.0
* **🎬 Cinematic Boot Sequence:** Proses startup bertahap (Warm-up -> Init -> Ready -> Greeting -> Scanning) tanpa gangguan interupsi.
* **🛡️ Guardian Mode:** Otomatisasi Kipas Laptop (Active LOW) berdasarkan kehadiran user (Presence Detection).
* **⚡ Handover Logic:** Transisi instan dari Booting ke Active Mode (Kipas langsung nyala jika user terdeteksi saat boot).
* **📡 OTA Firmware Update:** Update kodingan ESP32 via WiFi (Static IP `.200`).
* **❤️ Self-Healing System:** Script "Dokter" yang otomatis menghidupkan ulang sistem jika crash dan mendiagnosa error dari log.
* **🔊 Audio Stabilizer:** Manajemen sink Bluetooth dan audio ducking yang lebih halus.

---

## 🛠️ Hardware Requirements
1.  **Raspberry Pi Zero 2W** (Main Brain & MQTT Broker).
2.  **ESP32 Development Board** (Sensor Node & Controller).
3.  **HC-SR04** (Ultrasonic Distance Sensor).
4.  **DHT11** (Temperature & Humidity Sensor).
5.  **MQ-135** (Air Quality Sensor).
6.  **Relay Module 2-Channel:**
    * Channel 1: Laptop Cooling Fan (Logic: Active LOW).
    * Channel 2: Maintenance Lamp (Logic: Active HIGH).
7.  **Bluetooth Speaker** (Nanami's Voice).

---

## 🔌 Wiring Configuration (ESP32 Pinout)

Jangan sampai salah colok! Berikut pemetaan Pin GPIO di ESP32:

| Component | ESP32 Pin | Notes / Logic |
| :--- | :--- | :--- |
| **Laptop Fan Relay** | GPIO 26 | Active LOW (0 = ON) |
| **Maintenance Lamp** | GPIO 19 | Active HIGH (1 = ON) |
| **Buzzer** | GPIO 13 | Active HIGH |
| **Ultrasonic Trig** | GPIO 21 | Output |
| **Ultrasonic Echo** | GPIO 22 | Input |
| **DHT11 Sensor** | GPIO 4 | Pull-up Resistor required |
| **MQ-135 (Gas)** | GPIO 34 | Analog Input (ADC) |
| **RPi Power Control**| GPIO 27 | Optional (Transistor/Mosfet) |
  
---

## ⚙️ Installation Guide

### 1. Raspberry Pi Setup (The Brain)
Pastikan Python 3 dan Mosquitto Broker sudah terinstall.

```bash
# Clone Repository
git clone [https://github.com/USERNAME_LU/nanami-smartdesk.git](https://github.com/USERNAME_LU/nanami-smartdesk.git)
cd nanami-smartdesk

# Install Dependencies
pip3 install paho-mqtt gtts pyalsaaudio
sudo apt install mosquitto mosquitto-clients mpv pulseaudio-module-Bluetooth
```

Setup Cronjob (Auto-Start & Self-Heal): Buka crontab dengan crontab -e dan tambahkan baris ini di paling bawah:
```bash
# Jalanin Dokter Jaga tiap 1 menit (Wajib)
* * * * * python3 /home/rasphi/nanami/smartdesk_selfheal.py
```
Note: Script smartdesk_selfheal.py akan otomatis menjalankan smartdesk_core.py jika mati.

---

### 2. ESP32 Setup (The Nervous System)
Project ini menggunakan PlatformIO.

Buka folder project di VS Code + PlatformIO.

Edit src/main.cpp: Sesuaikan SSID, Password, dan IP MQTT Server.

Upload Pertama: Gunakan Kabel USB.

Upload Selanjutnya: Bisa via OTA (WiFi) dengan uncomment protokol espota di platformio.ini.

---

## 📡 MQTT Topic Dictionary

Daftar topik untuk integrasi manual via `mosquitto_sub/pub`:

### 📥 Sensors (ESP32 mengirim ke RPi)
* **Topic:** `smartdesk/sensor/data`
    * **Payload:** `{"dist": int, "temp": float, "gas": int}`
    * **Fungsi:** Data real-time jarak, suhu, dan kualitas udara.

### 📤 Controls (RPi memerintah ESP32)
* **Topic:** `smartdesk/control/fan`
    * **Payload:** `ON` / `OFF`
    * **Fungsi:** Menyalakan Kipas Laptop Otomatis (Active LOW).
* **Topic:** `smartdesk/control/lamp`
    * **Payload:** `ON` / `OFF`
    * **Fungsi:** Menyalakan Lampu Servis Manual (Active HIGH).
* **Topic:** `smartdesk/control/buzzer`
    * **Payload:** `1` - `5`
    * **Fungsi:** Membunyikan buzzer sebanyak n kali.

### 🔄 System Status
* **Topic:** `smartdesk/status`
    * **Payload:** `RPI_READY`
    * **Fungsi:** Sinyal bahwa RPi telah selesai booting (Trigger suara 'Tit-Tit').

---

### 🔧 Maintenance & Troubleshooting
Cara Cek Log (Diagnosa)
Jika Nanami diam atau error, cek log harian:

```bash
cat /home/rasphi/nanami/smartdesk.log
```

Atau cek log dokter jaga:
```bash
cat /home/rasphi/nanami/selfheal.log
```

---

Cara Update Firmware ESP32 (OTA)
- Pastikan ESP32 terhubung ke listrik.

- Di PlatformIO, pastikan upload_port = 192.168.1.200.

- Klik Upload. Tunggu hingga buzzer berbunyi "Tit" (Restart).

- Reset Audio Bluetooth
Jika suara hilang/putus-putus:
```bash
pulseaudio -k && pulseaudio --start
```
Lalu restart Nanami (atau tunggu Self-Heal bekerja).

---

Author: Chiko x Nanami AI

Version: 3.0 (Stable)

