# zenzone/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_FOLDER = os.environ.get("ZEN_UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# STT backend selection: "speech_recognition" (default) or "whisper" if you install/enable it
STT_BACKEND = os.environ.get("ZEN_STT_BACKEND", "speech_recognition")

# Text emotion model name (transformers). If not available, code falls back to rule-based.
EMOTION_MODEL = os.environ.get("ZEN_EMOTION_MODEL", "bhadresh-savani/distilbert-base-uncased-emotion")

# Database (SQLite) file path
DB_PATH = os.environ.get("ZEN_DB_PATH", os.path.join(BASE_DIR, "zenzone.db"))
