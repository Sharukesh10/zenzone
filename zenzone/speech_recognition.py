# zenzone/speech_recognition.py
import os
import logging
import shutil
import speech_recognition as sr
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available, falling back to Google Speech Recognition")
import tempfile
import subprocess
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def find_ffmpeg():
    """Find FFmpeg executable.

    Strategy:
    1. Check PATH using shutil.which for ffmpeg/ffmpeg.exe
    2. Check common installation directories
    Returns full path to ffmpeg executable or None.
    """
    # 1) Check PATH
    for exe_name in ("ffmpeg", "ffmpeg.exe"):
        ffmpeg_exe = shutil.which(exe_name)
        if ffmpeg_exe:
            logger.info(f"Found ffmpeg on PATH: {ffmpeg_exe}")
            return ffmpeg_exe

    # 2) Check common install locations
    possible_dirs = [
        r"C:\Program Files\ffmpeg\bin",
        r"C:\ffmpeg\bin",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-6.0-full_build\bin"),
        os.path.expandvars(r"%PROGRAMFILES%\ffmpeg\bin"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\ffmpeg\bin")
    ]

    for d in possible_dirs:
        ffmpeg_exe = os.path.join(d, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            logger.info(f"Found FFmpeg at: {ffmpeg_exe}")
            return ffmpeg_exe

    return None

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Initialize whisper model if available (using 'tiny' for faster loading)
        if WHISPER_AVAILABLE:
            try:
                logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("tiny")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load Whisper model: {e}")
                self.whisper_model = None
        else:
            self.whisper_model = None
            logger.info("Whisper not available, using Google Speech Recognition only")
        
        # Find FFmpeg executable and configure pydub to use it explicitly.
        ffmpeg_exe = find_ffmpeg()
        if ffmpeg_exe:
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            # Prepend ffmpeg dir to PATH so subprocesses can find it
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            # Ensure pydub uses the found ffmpeg binary directly
            try:
                AudioSegment.converter = ffmpeg_exe
                logger.info(f"Configured pydub AudioSegment.converter = {ffmpeg_exe}")
            except Exception as e:
                logger.warning(f"Failed to set pydub converter attribute: {e}")

            # Try to locate ffprobe too (used by pydub.mediainfo)
            ffprobe_exe = shutil.which("ffprobe") or os.path.join(ffmpeg_dir, "ffprobe.exe")
            if ffprobe_exe and os.path.exists(ffprobe_exe):
                os.environ["PATH"] = os.path.dirname(ffprobe_exe) + os.pathsep + os.environ.get("PATH", "")
                try:
                    # Some pydub functions rely on ffprobe being available on PATH
                    logger.info(f"ffprobe available: {ffprobe_exe}")
                except Exception:
                    pass
        else:
            logger.warning("FFmpeg not found. Please install FFmpeg and ensure it's on PATH.")

    def convert_to_wav(self, audio_path):
        """Convert audio file to WAV format if needed"""
        if audio_path.lower().endswith('.wav'):
            return audio_path
            
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_path = temp_wav.name
            
        try:
            # Try converting using pydub first
            logger.info(f"Converting {audio_path} to WAV format using pydub")
            try:
                audio = AudioSegment.from_file(audio_path)
                audio.export(temp_path, format='wav')
                logger.info(f"Successfully converted to WAV using pydub: {temp_path}")
                return temp_path
            except Exception as pydub_error:
                logger.warning(f"Pydub conversion failed: {pydub_error}, trying FFmpeg directly")
                
                # Try using FFmpeg directly
                logger.info("Attempting direct FFmpeg conversion")
                try:
                    result = subprocess.run(
                        ['ffmpeg', '-i', audio_path, '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1', temp_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info(f"Successfully converted to WAV using FFmpeg: {temp_path}")
                        return temp_path
                    else:
                        raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                except Exception as ffmpeg_error:
                    raise Exception(f"Both conversion methods failed. FFmpeg error: {ffmpeg_error}")
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
            raise Exception(f"Failed to convert audio to WAV format: {str(e)}")

    def transcribe_audio(self, audio_path):
        """
        Return text transcription of audio_path (wav or other).
        Tries Whisper first, falls back to Google Speech Recognition.
        """
        # Ensure we have a WAV file for recognizers
        wav_path = self.convert_to_wav(audio_path)
        
        # Try Whisper first (if available)
        if self.whisper_model is not None:
            try:
                result = self.whisper_model.transcribe(wav_path)
                text = result.get("text", "").strip()
                if text:
                    return text
                logger.warning("Whisper transcription returned empty result, falling back to Google Speech")
            except Exception as e:
                logger.warning(f"Whisper transcription failed: {e}, falling back to Google Speech")
        else:
            logger.info("Whisper not available, using Google Speech Recognition")
        
        # Fall back to Google Speech Recognition
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio)
            return text
        except Exception as e:
            logger.warning(f"Google Speech Recognition failed: {e}")
            return ""
        finally:
            # Clean up temporary WAV file if it was created
            if wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary WAV file: {e}")
