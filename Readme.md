# 🤖 Nanami Smart Desk (Hybrid IoT Edition)

**Nanami Smart Desk** adalah asisten desktop pintar berbasis IoT yang menggabungkan ESP32 (Sensor Node) dan Raspberry Pi (Logic Core). Sistem ini memiliki fitur *Presence Fusion*, *Audio Ducking*, dan *Health Monitoring*.

## 📂 Struktur Project
* `/arduino` : Firmware ESP32 (Dumb Node).
* `/raspi`   : Logic Python (Brain & Audio).
* `/service` : Auto-start script (Systemd).

## 🚀 Fitur Utama
1. **Fusion Presence**: Menggabungkan Ultrasonic + MQ135 + Suhu untuk deteksi manusia akurat (Anti-Ghosting).
2. **Auto Fan**: Kipas menyala otomatis saat user duduk, mati 10 detik setelah pergi.
3. **Contextual Voice**: Sapaan berbeda (Pagi/Siang/Malam) dengan aksen British.
4. **Volume Adaptif**: Suara keras di siang hari, senyap di malam hari.

## 🛠️ Cara Install
1. Flash `SmartDeskHub_Fusion.ino` ke ESP32.
2. Pindahkan file di folder `raspi` ke Raspberry Pi (`/home/rasphi/`).
3. Jalankan `python3 smart_greeting.py` sekali untuk generate suara.
4. Setup auto-start menggunakan file di folder `service`.

---
*Developed by Chiko Casillas | Engineering Student*