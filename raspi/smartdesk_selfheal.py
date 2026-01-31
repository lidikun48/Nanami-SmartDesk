import os
import time
import subprocess
import sys
from datetime import datetime

# --- CONFIG ---
TARGET_SCRIPT = "smartdesk_core.py"
WORK_DIR = "/home/rasphi/nanami/"
LOG_FILE = os.path.join(WORK_DIR, "smartdesk.log") # Pastikan ini sama dengan di core
SELFHEAL_LOG = os.path.join(WORK_DIR, "selfheal.log")

# --- AUDIO & ERROR CONFIG (DARI KODINGAN LU) ---
# Kita import aman biar kalau audio error, selfheal tetep jalan
try:
    sys.path.append(WORK_DIR)
    from smartdesk_audio import play_voice
except ImportError:
    def play_voice(f, t=None): pass # Dummy function

# Keyword Error (Punya Lu)
ERROR_KEYWORDS = {
    "Network unreachable": "system_error.mp3",
    "Audio device not found": "system_error.mp3",
    "Connection refused": "system_error.mp3",
    "OSError": "error.mp3"
}

# Pesan Custom (Punya Lu)
ERROR_MESSAGES = {
    "Network unreachable": "Network unavailable. Operating in limited mode.",
    "Audio device not found": "Audio system failure detected.",
    "Connection refused": "Sensor node disconnected."
}

# State buat Log Scanning
last_alert_time = {}

# --- FUNGSI 1: DOKTER UGD (Resusitasi) ---
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SELFHEAL_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def is_running(script_name):
    try:
        # Cek apakah script jalan di background
        output = subprocess.check_output(f"pgrep -f {script_name}", shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def revive_system():
    log_event(f"⚠️ ALERT: {TARGET_SCRIPT} is DOWN! Attempting CPR...")
    print(f"🚑 {TARGET_SCRIPT} mati! Menghidupkan ulang...")
    
    # Hidupkan ulang
    full_path = os.path.join(WORK_DIR, TARGET_SCRIPT)
    cmd = f"nohup python3 {full_path} > /dev/null 2>&1 &"
    os.system(cmd)
    
    time.sleep(5) 
    
    if is_running(TARGET_SCRIPT):
        log_event(f"✅ SUCCESS: {TARGET_SCRIPT} has been revived.")
    else:
        log_event(f"❌ CRITICAL: Failed to revive {TARGET_SCRIPT}.")

# --- FUNGSI 2: DOKTER DIAGNOSA (Scan Log - Punya Lu) ---
def scan_log():
    if not os.path.exists(LOG_FILE): return

    try:
        # Baca 20 baris terakhir
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()[-20:]

        now = time.time()

        for line in lines:
            for error_text, voice_key in ERROR_KEYWORDS.items():
                if error_text in line:
                    # Cek Cooldown (5 Menit)
                    if now - last_alert_time.get(error_text, 0) > 300:
                        print(f"🔧 [DIAGNOSA] Found Error: {error_text}")
                        log_event(f"🔧 Diagnosa Error: {error_text}")
                        
                        custom_msg = ERROR_MESSAGES.get(error_text, "System error detected.")
                        play_voice(voice_key, custom_msg)
                        
                        last_alert_time[error_text] = now

    except Exception as e:
        print(f"⚠️ Doctor Error: {e}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    # 1. Cek Nyawa Dulu (PENTING)
    if not is_running(TARGET_SCRIPT):
        revive_system()
    
    # 2. Kalau Hidup, Baru Cek Penyakit (Log)
    else:
        # print("❤️ System is running. Scanning logs...") # Uncomment buat debug
        scan_log()