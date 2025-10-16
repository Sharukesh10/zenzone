# zenzone/utils.py
import os
import uuid
from pydub import AudioSegment

def save_blob_to_file(blob_bytes, filename_hint="sample"):
    """
    Save raw bytes (from HTTP upload / webm) to a file in uploads, return path.
    Accepts filelike bytes (e.g., request.files['audio'].read()) or blob from JS.
    """
    from .config import UPLOAD_FOLDER
    ext = "webm"
    filename = f"{filename_hint}_{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    with open(path, "wb") as f:
        f.write(blob_bytes)
    return path

def convert_to_wav(in_path, out_path=None, sample_rate=22050):
    """
    Convert input audio file (webm/ogg/mp4/wav) -> WAV 16-bit mono at sample_rate.
    Returns out_path.
    """
    if out_path is None:
        base, _ = os.path.splitext(in_path)
        out_path = base + ".wav"
    # pydub uses ffmpeg underneath; ensure ffmpeg present on system
    audio = AudioSegment.from_file(in_path)
    audio = audio.set_frame_rate(sample_rate).set_channels(1).set_sample_width(2)
    audio.export(out_path, format="wav")
    return out_path
