import subprocess
import os

PIPER_MODEL = os.path.expanduser("~/lester/models/en_US-lessac-high.onnx")
OUTPUT_PATH = "static/speech.wav"

def speak(text):
    """Generate speech with Piper TTS — stateless, no crash risk."""
    os.makedirs("static", exist_ok=True)
    clean_text = text.replace('"', '\\"').replace("'", "\\'")
    cmd = f'echo "{clean_text}" | piper --model {PIPER_MODEL} --output_file {OUTPUT_PATH}'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        if result.returncode != 0:
            print(f"[TTS ERROR] {result.stderr.decode()}")
            return None
    except subprocess.TimeoutExpired:
        print("[TTS ERROR] Timed out")
        return None
    return f"/{OUTPUT_PATH}"

def speak_with_pause(text):
    """Add natural pauses between sentences."""
    processed = text.replace(". ", ".\\n")
    return speak(processed)
