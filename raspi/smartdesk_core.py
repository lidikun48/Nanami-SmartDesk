import time
import sys
import os
import json
import paho.mqtt.client as mqtt
from datetime import datetime

# --- IMPORT MODULE ---
try:
    from smartdesk_audio import play_voice, check_and_switch_audio
    from audio_config import LOG_FILE
except ImportError:
    sys.exit(1)

# --- CONFIG ---
MQTT_BROKER = "localhost"
MQTT_PORT   = 1883
MQTT_TOPIC  = "smartdesk/#"

# --- STATE VARIABLES ---
state = {
    "boot_complete": False,
    "mqtt_connected": False,
    "user_present": False,
    "fan_is_on": False,
    "last_error_time": 0,
    "away_timer_start": 0,
    "last_temp_alert": 0,
    "current_temp": -999,
    "current_dist": -999,
    "current_gas": 0
}

# --- LOGGER (Silent & Clean Mode) ---
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(LOG_FILE, "w") # Mode "w" = Reset log tiap restart
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self): pass

sys.stdout = Logger()

# --- HELPER ---
def get_time_greeting():
    h = datetime.now().hour
    if 0 <= h < 11:    return "greet_morning"
    elif 11 <= h < 16: return "greet_siang"
    elif 16 <= h < 19: return "greet_sore"
    else:              return "greet_malam"

def analyze_air(gas):
    if gas < 1500: return "Good"
    elif gas < 2500: return "Moderate"
    else: return "Bad"

# --- CINEMATIC DIRECTOR (Booting) ---
def run_cinematic_boot(client):
    print("\n🎬 STARTING CINEMATIC BOOT SEQUENCE...")
    
    check_and_switch_audio()
    time.sleep(1)
    play_voice("wake_up") 
    time.sleep(1)
    
    print("👉 Phase 1: Init")
    play_voice("boot")
    time.sleep(3)
    
    print("👉 Phase 2: Ready")
    play_voice("ready")
    time.sleep(2)
    
    print("👉 Phase 3: Greeting")
    play_voice(get_time_greeting())
    time.sleep(3)
    
    print("👉 Phase 4: Scanning")
    play_voice("scanning")
    
    print("⏳ Waiting for sensor data stream (Max 25s)...")
    max_wait = 25 # Diperlama buat kompensasi sinyal
    start_wait = time.time()
    
    got_data = False
    while time.time() - start_wait < max_wait:
        if state["current_temp"] != -999:
            got_data = True
            break
        time.sleep(0.5)
    
    print("👉 Phase 5: Reporting")
    if got_data:
        t = state["current_temp"]
        a = analyze_air(state["current_gas"])
        if t == -999:
             play_voice("sensor_fail")
        else:
             play_voice("sensor_report", f"Sensors connected. Temp {t}. Air {a}.")
    else:
        play_voice("sensor_fail", "Sensor connection timeout.")

    print("✅ BOOT COMPLETE. ENABLING GUARDIAN MODE.")
    
    # 1. Buka Kunci
    state["boot_complete"] = True
    client.publish("smartdesk/status", "RPI_READY", retain=True)
    
    # 2. 🔥 INITIAL CHECK / HANDOVER LOGIC 🔥
    # Langsung nyalain fan kalau user terdeteksi pas scanning tadi
    last_dist = state["current_dist"]
    if last_dist > 0 and last_dist < 80:
        print("👤 POST-BOOT CHECK: User detected! Activating FAN immediately.")
        state["user_present"] = True
        
        # Eksekusi FAN
        client.publish("smartdesk/control/fan", "ON")
        state["fan_is_on"] = True
        
        play_voice("welcome_back")

# --- MQTT EVENTS ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ MQTT Connected")
        client.subscribe(MQTT_TOPIC)
        state["mqtt_connected"] = True 

def on_message(client, userdata, msg):
    global state
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        if "sensor" in topic and "{" in payload:
            data = json.loads(payload)
            state["current_temp"] = data.get("temp", -999)
            state["current_dist"] = data.get("dist", -999)
            state["current_gas"]  = data.get("gas", 0)

            if not state["boot_complete"]: return 

            # --- VARIABLES ---
            dist = state["current_dist"]
            temp = state["current_temp"]

            # 1. RUNTIME WATCHDOG
            if (temp == -999 or dist == -999):
                if time.time() - state["last_error_time"] > 300:
                    print("⚠️ SENSOR FAILURE!")
                    play_voice("runtime_error")
                    state["last_error_time"] = time.time()

            # 2. PRESENCE LOGIC (THE BRAIN)
            if dist != -999:
                # --- USER DATANG ---
                if dist > 0 and dist < 80:
                    state["away_timer_start"] = 0
                    
                    if not state["user_present"]:
                        print(f"👤 USER ARRIVED")
                        state["user_present"] = True
                        
                        # A. Sapaan Instan
                        play_voice("welcome_back")
                        
                        # B. Briefing Lengkap
                        now_jam = datetime.now().strftime("%H:%M")
                        briefing_text = f"Current time is {now_jam}. Room temperature is {temp} degrees. Air quality is {analyze_air(state['current_gas'])}."
                        print(f"🔊 Briefing: {briefing_text}")
                        play_voice("dynamic_briefing", briefing_text)

                        # C. Nyalain FAN LAPTOP (Otomatis)
                        if not state["fan_is_on"]:
                            client.publish("smartdesk/control/fan", "ON")
                            state["fan_is_on"] = True

                # --- USER PERGI ---
                elif dist >= 80 or dist == 0:
                    if state["user_present"]:
                        if state["away_timer_start"] == 0:
                            state["away_timer_start"] = time.time()
                        elif time.time() - state["away_timer_start"] > 5:
                            print("💨 USER LEFT")
                            state["user_present"] = False
                            state["away_timer_start"] = 0
                            
                            play_voice("bye")
                            
                            # Matiin FAN LAPTOP (Otomatis)
                            if state["fan_is_on"]:
                                client.publish("smartdesk/control/fan", "OFF")
                                state["fan_is_on"] = False

            # 3. SAFETY
            if temp > 34 and temp != -999:
                if time.time() - state["last_temp_alert"] > 60:
                    play_voice("temp_alert", f"High temperature {temp} degrees.")
                    state["last_temp_alert"] = time.time()

    except Exception as e:
        pass 

if __name__ == "__main__":
    print(f"\n🚀 Nanami 'Director Cut' v3.5 Starting... {datetime.now()}")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start() 
    
    while not state["mqtt_connected"]:
        time.sleep(0.1)
    
    run_cinematic_boot(client)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()
        print("🛑 System Offline.")