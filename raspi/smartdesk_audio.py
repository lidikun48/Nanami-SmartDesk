import os
import time
import subprocess
from audio_config import VOICE_DIR

try:
    from smart_greeting import ensure_voice
except ImportError:
    ensure_voice = None

current_sink = None

def check_and_switch_audio():
    global current_sink
    try:
        cmd = "pactl list short sinks | grep bluez"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        if output:
            bt_sink = output.split()[1]
            if bt_sink != current_sink:
                os.system(f"pactl set-default-sink {bt_sink} 2>/dev/null")
                current_sink = bt_sink
    except:
        pass

def duck_music(state="ON"):
    try:
        vol = "40%" if state == "ON" else "100%"
        cmd = "pactl list sink-inputs short | awk '{print $1}'"
        inputs = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip().split('\n')
        for idx in inputs:
            if idx:
                os.system(f"pactl set-sink-input-volume {idx} {vol} 2>/dev/null")
    except:
        pass

def play_mp3(path):
    if os.path.exists(path):
        check_and_switch_audio()
        duck_music("ON")
        time.sleep(0.1)
        os.system(f"mpv --no-terminal --msg-level=all=no --volume=100 --audio-device=auto '{path}' 2>/dev/null")
        time.sleep(0.1)
        duck_music("OFF")

def play_voice(filename, text_fallback=None):
    if not filename.endswith(".mp3"): filename += ".mp3"
    
    if "/" in filename:
        path = filename
        key_name = os.path.splitext(os.path.basename(filename))[0]
    else:
        path = os.path.join(VOICE_DIR, filename)
        key_name = filename.replace(".mp3", "")

    if os.path.exists(path):
        play_mp3(path)
        return

    if ensure_voice:
        new_path = ensure_voice(key_name, text_fallback)
        if new_path and os.path.exists(new_path):
            play_mp3(new_path)
        else:
            err_path = os.path.join(VOICE_DIR, "net_error.mp3")
            if os.path.exists(err_path): play_mp3(err_path)