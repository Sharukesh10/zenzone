"""
ZenZone - AI-Powered Stress Detection and Mindfulness Application

Module Structure:
- routes.py: Web API routes and endpoints
- database.py: Database connection and configuration
- database_models.py: SQLAlchemy models for data storage
- emotion_analyzer.py: Emotion and stress detection using ML
- speech_recognition.py: Speech-to-text conversion
- activity_suggestions.py: Calming activity recommendations
- audio_processor.py: Audio file processing and analysis
- helpers.py: Utility functions and common helpers
- config.py: Application configuration
"""

# Define what the package exports
__all__ = ['EmotionAnalyzer', 'SpeechToText', 'get_activity_suggestion']

# Import the components
from .emotion_analyzer import EmotionAnalyzer
from .speech_recognition import SpeechToText
from .activity_suggestions import get_activity_suggestion

# Version of the ZenZone package
__version__ = '1.0.0'
