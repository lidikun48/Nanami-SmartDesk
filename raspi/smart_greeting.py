## smart_greeting.py
## Nanami Voice Factory v3.0 (Smart QC)
## Author: Chiko x Nanami

import os
import time
import sys
from gtts import gTTS
from audio_config import VOICE_DIR

PHRASES = {
    # === SYSTEM CORE ===
    "wake_up":       "Audio system online.",
    "boot":          "System initialized. Core services active.",
    "ready":         "All systems checks complete. Ready to serve.",

    # === GREETING WAKTU ===
    "greet_morning": "Good morning, Sir. Have a great activity.",
    "greet_siang":   "Good afternoon, Sir. Hope your day is going well.",
    "greet_sore":    "Good afternoon, Sir. It is getting late.",
    "greet_malam":   "Good evening, Sir. System running in night mode.",

    # === STATUS ===
    "scanning":      "Scanning for sensor modules...",
    "sensor_fail":   "Alert. Sensor malfunction detected.",
    "runtime_error": "Warning. Sensor failure during operation.",
    "sensor_report": "Sensors connected.", # Fallback text

    # === PRESENCE ===
    "welcome_back":  "Welcome back, Sir.",
    "bye":           "User left. Goodbye.",

    # === ALERTS ===
    "temp_alert":    "Warning. High temperature detected.",
    "asset_missing": "Audio asset missing. Generating replacement.",
    "net_error":     "Network error."
}

def validate_asset(path):
    """
    Quality Control: Cek apakah file ada DAN isinya valid (bukan 0 kb).
    Return: True (Valid), False (Rusak/Hilang)
        """
    if os.path.exists(path):
        # Cek ukuran file. Kalau di bawah 100 bytes, anggap rusak/kosong.
        if os.path.getsize(path) > 100:
            return True
        else:
            print(f"🗑️ Found corrupt asset: {path}. Deleting..." )
            os.remove(path) # Hapus file sampah
            return False
    return False

def ensure_voice(key, text=None):
    """
    Fungsi Pabrik dengan Auto-Retry & Quality Control
    """
    path = os.path.join(VOICE_DIR, f"{key}.mp3")

    # 1. QUALITY CONTROL (Cek sebelum bikin)
    # Kalau file udah ada dan valid, gak usah bikin (kecuali dipaksa text custom)
    if validate_asset(path) and text is None:
        return path

    if text is None:
        text_to_say = PHRASES.get(key, f"Audio asset {key} missing.")
    else:
        text_to_say = text

    # 2. PROSES PRODUKSI (Dengan Retry)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🎤 Factory: Generating '{key}'... (Attempt {attempt}/{max_retries})")
            tts = gTTS(text=text_to_say, lang='en', tld='co.uk')
            tts.save(path)

            # 3. VERIFIKASI AKHIR (Pastikan file beneran ke-save)
            if validate_asset(path):
                print(f"✅ Asset '{key}' Created & Verified!")
                return path
            else:
                print("⚠️ File created but seems corrupt. Retrying...")

        except Exception as e:
            print(f"⚠️ Generation Failed: {e}")
            if attempt < max_retries:
                print("⏳ Connection unstable. Waiting 2s...")
                time.sleep(2)
            else:
                print(f"❌ Giving up on '{key}'. Check internet.")
                return None

# --- ALIAS ---
generate_voice = ensure_voice

# --- MAIN EXECUTION (MASS PRODUCTION) ---
if __name__ == "__main__":
    print("🏭 Starting Smart Factory (Quality Control Mode)...")
    print("---------------------------------------------------")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for key in PHRASES:
        path = os.path.join(VOICE_DIR, f"{key}.mp3")

        # Cek dulu, kalau udah ada dan bagus, SKIP.
        if validate_asset(path):
            print(f"⏩ Skipping '{key}' (Good condition).")
            skip_count += 1
            continue

        # Kalau belum ada / rusak, GENERATE.
        result = ensure_voice(key)
        if result:
            success_count += 1
        else:
            fail_count += 1

    print("---------------------------------------------------")
    print(f"📊 REPORT: Skipped: {skip_count} | Created: {success_count} | Failed: {fail_count}")

    if fail_count > 0:
        print("💡 Tip: Run this script again to retry failed assets.")
    else:
        print("✅ All assets are 100% ready.")