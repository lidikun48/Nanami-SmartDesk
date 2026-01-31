import os

# Deteksi Home User (~/rasphi)
HOME = os.path.expanduser("~")

# Base Folder Project (dimana script berada)
BASE = os.path.join(HOME, "nanami")

# [UPDATE] Sekarang arahkan ke dalam folder BASE (nanami), bukan HOME
VOICE_DIR = os.path.join(BASE, "voice")
MUSIC_DIR = os.path.join(BASE, "music")
LOG_DIR = os.path.join(BASE, "logs")       # Folder log
LOG_FILE = os.path.join(LOG_DIR, "system.log") # File log di DALAM folder

# Pastikan folder ada (buat jaga-jaga)
os.makedirs(VOICE_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(BASE, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)