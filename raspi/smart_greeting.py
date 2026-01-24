## smart_greeting.py
## Jalanin ulang: python3 smart_greeting.py

from gtts import gTTS
import os

SOUND_DIR = "/home/rasphi/sounds"
os.makedirs(SOUND_DIR, exist_ok=True)

PHRASES = {
    # System
    "boot":          "System online. Welcome back, Sir.",

    # Sapaan Waktu
    "greet_morning": "Good morning, Sir. Have a great day.",
    "greet_day":     "Good afternoon, Sir. Welcome back.",
    "greet_evening": "Good evening. Don't forget to rest.",

    # User Pergi
    "bye":           "Goodbye, Sir. See you later.",

    # Health & Safety (SUDAH ADA)
    "air_alert":     "Warning. Air quality is dropping.",
    "hydrate":       "You have been seated for over an hour. Please drink some water.",

    # Bluetooth (BARU DITAMBAH)
    "bt_connect":    "Bluetooth audio connected.",
    "bt_disconnect": "Bluetooth disconnected."
}

def generate_voice():
    print("🎤 NANAMI VOICE GENERATOR UPDATING...")

    for filename, text in PHRASES.items():
        fullpath = f"{SOUND_DIR}/{filename}.mp3"

        # Hapus file lama kalau mau update teks, atau skip kalau udah ada
        if os.path.exists(fullpath):
            print(f"   ⏩ {filename}.mp3 exists (Skipping)")
            continue

        print(f"   generating: {filename}...")
        
        tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
        tts.save("temp_raw.mp3")

        # Boost Volume & Tempo
        cmd = f'ffmpeg -y -v error -i temp_raw.mp3 -filter:a "volume=1.3,atempo=1.15" {fullpath}'
        os.system(cmd)

    if os.path.exists("temp_raw.mp3"):
        os.remove("temp_raw.mp3")
    print("✅ All voices updated.")

if __name__ == "__main__":
    generate_voice()