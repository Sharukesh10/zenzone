"""
ZenZone Audio Processor Module

This module handles audio file processing and feature extraction for stress analysis.
"""

import os
import tempfile
import logging
import numpy as np
import librosa
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def preprocess_audio(audio_path):
    """
    Preprocess an audio file for analysis by:
    - Converting to WAV format if needed
    - Converting to mono if stereo
    - Standardizing sample rate
    - Normalizing volume
    - Trimming silence
    
    Args:
        audio_path: Path to the input audio file
        
    Returns:
        Path to the processed audio file
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
            
        # Set standard sample rate (16kHz is good for speech)
        audio = audio.set_frame_rate(16000)
        
        # Normalize volume
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio.dBFS
        audio = audio.apply_gain(change_in_dBFS)
        
        # Strip silence from beginning and end
        silence_thresh = -50  # dB
        audio = audio.strip_silence(
            silence_len=500,  # ms
            silence_thresh=silence_thresh,
            padding=100  # ms of silence to keep
        )
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_path = temp_wav.name
            audio.export(temp_path, format='wav')
            
        return temp_path
        
    except Exception as e:
        logger.error(f"Error preprocessing audio file: {e}")
        return audio_path  # Return original file on error

def extract_features(audio_path, sr_target=22050):
    """
    Extract acoustic features relevant to stress detection.
    
    Args:
        audio_path: Path to the audio file (should be WAV)
        sr_target: Target sample rate for analysis (default: 22050 Hz)
        
    Returns:
        Dictionary containing extracted features and their normalized values
    """
    try:
        # Load audio file using librosa
        y, sr = librosa.load(audio_path, sr=sr_target)
        
        # Extract various audio features
        features = {}
        
        # 1. RMS Energy (volume/intensity)
        rms = librosa.feature.rms(y=y)
        features['rms_mean'] = float(np.mean(rms))
        features['rms_std'] = float(np.std(rms))
        
        # 2. Spectral Centroid (brightness/sharpness)
        cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        features['centroid_mean'] = float(np.mean(cent))
        features['centroid_std'] = float(np.std(cent))
        
        # 3. Tempo/Speech Rate
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features['tempo'] = float(tempo)
        
        # 4. Pitch statistics using fundamental frequency
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        if len(pitch_values) > 0:
            features['pitch_mean'] = float(np.mean(pitch_values))
            features['pitch_std'] = float(np.std(pitch_values))
        else:
            features['pitch_mean'] = 0.0
            features['pitch_std'] = 0.0
        
        # 5. Spectral Rolloff (energy distribution)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        features['rolloff_mean'] = float(np.mean(rolloff))
        
        # Normalize features to 0-100 scale for easier interpretation
        normalized_features = {
            'volume': min(100, max(0, features['rms_mean'] * 1000)),
            'pitch': min(100, max(0, features['pitch_mean'] / 20)),
            'speech_rate': min(100, max(0, features['tempo'] / 2)),
            'voice_variability': min(100, max(0, features['pitch_std'] * 10)),
            'energy_distribution': min(100, max(0, features['rolloff_mean'] / 100))
        }
        
        return normalized_features
        
    except Exception as e:
        logger.error(f"Error extracting features from audio file {audio_path}: {str(e)}")
        # Return default values if processing fails
        return {
            'volume': 50,
            'pitch': 50,
            'speech_rate': 50,
            'voice_variability': 50,
            'energy_distribution': 50
        }

def process_audio(audio_path, sr_target=22050):
    """
    Complete audio processing pipeline: preprocess audio and extract features.
    
    Args:
        audio_path: Path to the input audio file
        sr_target: Target sample rate for analysis
        
    Returns:
        Dictionary containing normalized audio features
    """
    try:
        # Step 1: Preprocess the audio file
        processed_path = preprocess_audio(audio_path)
        
        # Step 2: Extract features from the processed audio
        features = extract_features(processed_path, sr_target)
        
        # Clean up temporary file if one was created
        if processed_path != audio_path:
            try:
                os.remove(processed_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {processed_path}: {e}")
        
        return features
        
    except Exception as e:
        logger.error(f"Error in audio processing pipeline: {e}")
        return {
            'volume': 50,
            'pitch': 50,
            'speech_rate': 50,
            'voice_variability': 50,
            'energy_distribution': 50
        }
