import numpy as np
import librosa
import logging

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """Emotion analyzer that lazy-loads the transformers pipeline to avoid
    heavy imports and model downloads during module import.
    """
    def __init__(self, model_name: str = "bhadresh-savani/distilbert-base-uncased-emotion"):
        # Defer importing transformers.pipeline and model initialization until needed
        self.emotion_model = None
        self.model_name = model_name

        # Emotion mapping to stress scores
        self.emotion_stress_map = {
            'joy': 10,        # Calm/Happy
            'sadness': 50,    # Moderate stress
            'anger': 90,      # High stress
            'fear': 80,       # High stress
            'surprise': 40,   # Mild stress
            'neutral': 30     # Low stress
        }

    def _load_model(self):
        """Load the transformers pipeline on first use."""
        if self.emotion_model is not None:
            return
        try:
            from transformers import pipeline
            logger.info("Loading emotion detection model: %s", self.model_name)
            self.emotion_model = pipeline(
                "text-classification",
                model=self.model_name
            )
            logger.info("Emotion model loaded")
        except Exception as e:
            logger.warning("Failed to load emotion model: %s", e)
            self.emotion_model = None

    def analyze_text(self, text):
        """Analyze text for emotion and stress level.

        This will attempt to lazy-load the model if it's not yet available.
        If the model cannot be loaded, a sensible default is returned.
        """
        if not text:
            return {'emotion': 'neutral', 'stress_score': 30}

        # Ensure model is loaded
        self._load_model()
        if not self.emotion_model:
            logger.warning("Emotion model unavailable, falling back to neutral")
            return {'emotion': 'neutral', 'stress_score': 30}

        try:
            result = self.emotion_model(text)[0]
            emotion = result['label']
            confidence = result.get('score', 1.0)

            # Map emotion to stress score
            base_stress_score = self.emotion_stress_map.get(emotion, 50)
            # Adjust stress score based on confidence
            adjusted_stress_score = base_stress_score * confidence

            return {
                'emotion': emotion,
                'stress_score': min(100, adjusted_stress_score)
            }
        except Exception as e:
            logger.error("Error running emotion model: %s", e)
            return {'emotion': 'neutral', 'stress_score': 30}

    def analyze_audio_features(self, audio_path):
        """Extract and analyze audio features for stress indicators."""
        try:
            # Load audio file
            y, sr = librosa.load(audio_path)
            
            # Extract features
            # 1. Volume/energy variations
            rms = librosa.feature.rms(y=y)[0]
            
            # 2. Pitch variations
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # 3. Speech rate (zero crossing rate as proxy)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            # Calculate stress indicators
            volume_stress = np.mean(rms) * 100
            pitch_stress = np.mean(magnitudes) * 100
            rate_stress = np.mean(zcr) * 100
            
            # Combine features into overall stress score
            audio_stress_score = np.mean([volume_stress, pitch_stress, rate_stress])
            
            return {
                'audio_stress_score': min(100, audio_stress_score),
                'features': {
                    'volume': float(np.mean(rms)),
                    'pitch': float(np.mean(magnitudes)),
                    'speech_rate': float(np.mean(zcr))
                }
            }
        except Exception as e:
            print(f"Error analyzing audio: {str(e)}")
            return {
                'audio_stress_score': 50,
                'features': {}
            }

    def get_activity_suggestion(self, stress_score):
        """Get activity suggestion based on stress score."""
        if stress_score < 30:
            return {
                'type': 'music',
                'title': 'Enjoy Some Lo-fi Music',
                'description': 'Your stress levels are low. Why not maintain this calm state with some soothing lo-fi music?'
            }
        elif stress_score < 50:
            return {
                'type': 'breathing',
                'title': '2-Minute Breathing Exercise',
                'description': 'Take a short breathing break to maintain your balance.'
            }
        elif stress_score < 70:
            return {
                'type': 'meditation',
                'title': 'Quick Body Scan Meditation',
                'description': 'A guided body scan can help reduce your building stress.'
            }
        else:
            return {
                'type': 'nature',
                'title': 'Nature Sound Break',
                'description': 'Your stress levels are high. Take a moment to listen to calming nature sounds.'
            }

    def analyze(self, text, audio_path=None):
        """Perform complete analysis of text and audio."""
        # Analyze text emotion
        text_analysis = self.analyze_text(text)
        
        # Analyze audio if provided
        audio_analysis = (
            self.analyze_audio_features(audio_path)
            if audio_path else {'audio_stress_score': 50, 'features': {}}
        )
        
        # Combine scores (weighted average)
        final_stress_score = (
            text_analysis['stress_score'] * 0.6 +
            audio_analysis['audio_stress_score'] * 0.4
        )
        
        # Get activity suggestion
        activity = self.get_activity_suggestion(final_stress_score)
        
        return {
            'stress_score': round(final_stress_score, 2),
            'emotion': text_analysis['emotion'],
            'audio_features': audio_analysis['features'],
            'activity': activity
        }
