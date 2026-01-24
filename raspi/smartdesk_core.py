#!/usr/bin/env python3
# Simpan di: /home/rasphi/smartdesk_core.py

import paho.mqtt.client as mqtt
import time
import os
import json
import subprocess
import threading
from datetime import datetime
from gtts import gTTS

# ================= CONFIG =================
BROKER = "localhost"
TOPIC_DATA     = "desk/sensor/data"
TOPIC_STATE    = "desk/system/state"
TOPIC_CTRL_FAN = "desk/control/fan"  # Topik buat nyalain Kipas

SOUND_DIR = "/home/rasphi/sounds"
MQ_THRESHOLD_BAD = 2200
CONFIDENCE_LIMIT = 65

# Volume & State
VOL_DAY   = "85%"
VOL_NIGHT = "35%"
CURRENT_VOL_MODE = ""

SYSTEM_READY = False
USER_PRESENT = False
BLUETOOTH_CONNECTED = False
LAST_SEEN = 0
SEATED_START = 0
LAST_HEALTH_CHECK = 0
AIR_WARNING_LEVEL = 0
LAST_AIR_WARN = 0

# ================= 🔊 AUDIO & VOLUME =================
def set_master_volume():
    global CURRENT_VOL_MODE
    h = datetime.now().hour
    target = VOL_DAY if 6 <= h < 23 else VOL_NIGHT
    mode = "DAY" if 6 <= h < 23 else "NIGHT"
    
    if CURRENT_VOL_MODE != mode:
        os.system(f"amixer -D pulse sset Master {target} > /dev/null")
        CURRENT_VOL_MODE = mode

def duck_audio(active=True):
    try:
        cmd = "pactl list sink-inputs short | grep loopback | awk '{print $1}'"
        streams = subprocess.getoutput(cmd).split('\n')
        vol = "25%" if active else "100%"
        for sid in streams:
            if sid: os.system(f"pactl set-sink-input-volume {sid} {vol}")
    except: pass

def play_voice(filename_or_text, is_dynamic=False):
    set_master_volume()
    duck_audio(True)

    if is_dynamic:
        tts = gTTS(text=filename_or_text, lang='en', tld='co.uk', slow=False)
        tts.save("/tmp/nanami_temp.mp3")
        os.system("mpg123 -q /tmp/nanami_temp.mp3")
    else:
        path = f"{SOUND_DIR}/{filename_or_text}.mp3"
        if os.path.exists(path): os.system(f"mpg123 -q {path}")

    duck_audio(False)

# ================= 📱 BLUETOOTH MONITOR =================
def monitor_bluetooth():
    global BLUETOOTH_CONNECTED
    while True:
        try:
            cmd = "pactl list sources short | grep bluez_source"
            is_connected = "bluez_source" in subprocess.getoutput(cmd)

            if is_connected != BLUETOOTH_CONNECTED:
                if is_connected:
                    time.sleep(1)
                    play_voice("bt_connect")
                else:
                    play_voice("bt_disconnect")
                                BLUETOOTH_CONNECTED = is_connected
        except: pass
        time.sleep(2)

# ================= 🧠 LOGIC ENGINE =================
def calculate_confidence(dist, mq, temp):
    score = 0
    if dist < 80: score += 60
    if mq > 1200: score += 30
    if temp > 29: score += 10
    return min(score, 100)

def check_health(duration):
    global LAST_HEALTH_CHECK
    if duration > 3600 and (time.time() - LAST_HEALTH_CHECK > 3600):
        play_voice("hydrate")
        LAST_HEALTH_CHECK = time.time()

def check_air_quality(mq_val):
    global AIR_WARNING_LEVEL, LAST_AIR_WARN
    if mq_val < MQ_THRESHOLD_BAD:
        AIR_WARNING_LEVEL = 0
        return
    now = time.time()
    if now - LAST_AIR_WARN < 300: return

    if AIR_WARNING_LEVEL == 0:
        play_voice("air_alert")
        AIR_WARNING_LEVEL = 1
    elif AIR_WARNING_LEVEL == 1:
        play_voice("Air quality is critical. Please ventilate.", True)
        AIR_WARNING_LEVEL = 2
    LAST_AIR_WARN = now

# ================= 📡 MQTT CALLBACKS =================
def on_message(client, userdata, msg):
    global USER_PRESENT, LAST_SEEN, SEATED_START
    if not SYSTEM_READY: return

    try:
        data = json.loads(msg.payload.decode())
                dist = data.get('d', 999)
        mq   = data.get('mq', 0)
        temp = data.get('t', 0)

        confidence = calculate_confidence(dist, mq, temp)
        now = time.time()

        # === USER DATANG (Presence Detect) ===
        if confidence >= CONFIDENCE_LIMIT and not USER_PRESENT:
            USER_PRESENT = True
            SEATED_START = now
            LAST_SEEN = now

            # 1. AUTO NYALAIN KIPAS (Lampu Tetap Manual)
            client.publish(TOPIC_CTRL_FAN, "ON")

            # 2. Sapaan Nanami
            h = datetime.now().hour
            if 5 <= h < 12: play_voice("greet_morning")
            elif 12 <= h < 18: play_voice("greet_day")
            else: play_voice("greet_evening")

            time.sleep(0.5)
            play_voice(f"Current room temperature is {int(temp)} degrees.", True)

        # === USER DUDUK (Monitoring) ===
        elif confidence >= CONFIDENCE_LIMIT and USER_PRESENT:
            LAST_SEEN = now
            check_health(now - SEATED_START)
            check_air_quality(mq)

        # === USER PERGI (Auto OFF) ===
        elif confidence < 40 and USER_PRESENT:
            if (now - LAST_SEEN) > 10: # Tunggu 10 Detik
                USER_PRESENT = False
                play_voice("bye")

                # MATIKAN KIPAS
                client.publish(TOPIC_CTRL_FAN, "OFF")

    except Exception as e:
        print(f"Error: {e}")

def on_connect(client, userdata, flags, rc):
    global SYSTEM_READY
    client.subscribe(TOPIC_DATA)
    set_master_volume()
    play_voice("boot")
    client.publish(TOPIC_STATE, "RPI_READY")
    SYSTEM_READY = True

if __name__ == "__main__":
    os.environ["PULSE_RUNTIME_PATH"] = "/run/user/1000/pulse"

    # Start Bluetooth Thread
    threading.Thread(target=monitor_bluetooth, daemon=True).start()

    # Start MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, 1883, 60)
        client.loop_forever()
    except KeyboardInterrupt: pass