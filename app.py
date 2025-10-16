# app.py
import os
import tempfile
import logging
import numpy as np
import librosa
import scipy.signal as _scipy_signal
from flask import Flask, request, jsonify, render_template

from zenzone.emotion_analyzer import EmotionAnalyzer
from zenzone.speech_recognition import SpeechToText
from zenzone.activity_suggestions import get_activity_suggestion
from zenzone.supabase_client import insert_session

# Compatibility shim: older/newer SciPy versions place window functions differently.
# Some libraries (librosa and others) expect `scipy.signal.hann` to exist.
# If it's missing, provide a fallback to `scipy.signal.windows.hann` or numpy.hanning.
if not hasattr(_scipy_signal, 'hann'):
    try:
        # prefer scipy.signal.windows.hann if available
        _scipy_signal.hann = _scipy_signal.windows.hann
    except Exception:
        # final fallback to numpy.hanning
        _scipy_signal.hann = np.hanning

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and configure upload folder
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize the speech recognition and emotion analyzer
speech_to_text = SpeechToText()
emotion_analyzer = EmotionAnalyzer()

def compute_voice_features(audio_path, sr_target=22050):
    """Extract audio features for stress analysis"""
    try:
        # Load and analyze the audio file
        y, sr = librosa.load(audio_path, sr=sr_target)
        
        # Extract audio features
        rms = np.mean(librosa.feature.rms(y=y))
        cent = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Normalize features to 0-100 scale
        rms_score = float(np.clip((rms / 0.02) * 100, 0, 100))
        cent_score = float(np.clip((cent / 2000) * 100, 0, 100))
        tempo_score = float(np.clip((tempo / 180) * 100, 0, 100))
        
        return {
            "rms": rms_score,        # Volume/intensity
            "centroid": cent_score,  # Pitch/brightness
            "tempo": tempo_score     # Speech rate
        }
    except Exception as e:
        logger.error(f"Error computing voice features: {e}")
        return {"rms": 50, "centroid": 50, "tempo": 50}  # Default values on error

def combine_scores(text_score, voice_features):
    """Combine text-based emotion score with voice features into final stress score"""
    try:
        # Weight the influence of voice features
        voice_influence = (
            voice_features['rms'] * 0.4 +      # Volume has strong impact
            voice_features['centroid'] * 0.4 +  # Pitch has strong impact
            voice_features['tempo'] * 0.2       # Speed has moderate impact
        ) / 100.0
        
        # Combine scores - voice can adjust base score up to ±30 points
        stress = text_score + ((voice_influence - 0.5) * 60)
        return float(np.clip(stress, 0, 100))
        
    except Exception as e:
        logger.error(f"Error combining scores: {e}")
        return text_score  # Fall back to text-only score on error

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    temp_file = None
    try:
        # Expects 'audio' file in form data
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400
            
        audio_file = request.files['audio']
        if not audio_file or not audio_file.filename:
            return jsonify({"error": "No file selected"}), 400
            
        # Save to a temporary file with the correct extension
        _, ext = os.path.splitext(audio_file.filename)
        if not ext:
            ext = '.webm'  # Default extension for browser audio recording
            
        # Create a temporary file that won't be deleted immediately
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        audio_file.save(temp_file.name)
        temp_file.close()
        
        if not os.path.exists(temp_file.name):
            return jsonify({"error": "Failed to save audio file"}), 500
            
        # Store the filename for use in the rest of the function
        filename = temp_file.name
        logger.info(f"Saved uploaded file as: {filename}")
            
        try:
            # 1) Speech -> text using our speech recognition class
            text = speech_to_text.transcribe_audio(filename)
            if not text:
                logger.warning("No text transcribed from audio")
            logger.info(f"Transcribed text: {text}")

            # 2) Analyze emotion using our emotion analyzer
            emotion_result = emotion_analyzer.analyze_text(text if text else "")
            stress_score = emotion_result.get('stress_score', 50)
            emotion_label = emotion_result.get('emotion', 'neutral')
            logger.info(f"Emotion analysis: {emotion_label} (stress score: {stress_score})")
            
            # 3) Extract audio features for additional analysis
            voice_features = compute_voice_features(filename)
            logger.info(f"Voice features: {voice_features}")
            
            # 4) Combine text-based and audio-based analysis
            final_stress = combine_scores(stress_score, voice_features)
            
            # 5) Get activity suggestion based on final stress score
            suggestion = get_activity_suggestion(final_stress)
            friendly_label = suggestion['title']  # Use the title from suggestion as friendly label

            response = {
                "text": text,
                "emotion": emotion_label,
                "friendly_label": friendly_label,
                "stress_score": round(float(final_stress), 1),
                "suggestion": suggestion,
                "audio_features": voice_features
            }

            # --- SUPABASE: Save session ---
            try:
                # You can replace 'user_id' with a real user identifier if available
                insert_session(
                    user_id="anonymous",  # Replace with real user id if you have auth
                    stress_score=round(float(final_stress), 1),
                    emotion=emotion_label,
                    transcribed_text=text
                )
            except Exception as supabase_error:
                logger.warning(f"Supabase insert failed: {supabase_error}")
            # --- END SUPABASE ---

            return jsonify(response)
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}", exc_info=True)
            return jsonify({"error": "Error processing audio: " + str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error: " + str(e)}), 500
        
    finally:
        # Clean up any temporary files
        try:
            if temp_file and os.path.exists(temp_file.name):
                os.remove(temp_file.name)
                logger.debug(f"Cleaned up temporary file: {temp_file.name}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")



if __name__ == "__main__":
    from flask_cors import CORS
    CORS(app)
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

