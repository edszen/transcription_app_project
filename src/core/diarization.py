import logging
import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
from src import config
import whisperx
from src.utils.encryption import EncryptionUtils
import pandas as pd

logger = logging.getLogger(__name__)

def count_speakers(segments):
    """
    Count the number of unique speakers in the segments.
    """
    unique_speakers = set(segment.get('speaker', 'UNKNOWN') for segment in segments)
    speaker_count = len(unique_speakers)
    logger.info(f"Detected {speaker_count} unique speakers")
    return speaker_count

def apply_diarization(audio_path, encrypted_api_key, vad_segments, embeddings, transcription):
    try:
        logger.info("Starting speaker diarization")
        
        # Handle the case of a single segment/speaker
        if len(embeddings) == 1:
            logger.info("Single segment/speaker detected, assigning a single speaker.")
            return [{"start": vad_segments[0][0],
                     "end": vad_segments[0][1],
                     "speaker": "Speaker_0"
                     }]
        
        # Normalize embeddings
        scaler = StandardScaler()
        normalized_embeddings = scaler.fit_transform(embeddings)
        
        # Perform clustering
        clustering = AgglomerativeClustering(
            n_clusters=min(len(embeddings), config.MAX_SPEAKERS),
            metric='euclidean',
            linkage='ward'
        )
        labels = clustering.fit_predict(normalized_embeddings)
        
        # Initialize WhisperX
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Decrypt the API key
        encryption_utils = EncryptionUtils()
        api_key = encryption_utils.decrypt(encrypted_api_key)
        
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Load diarization model
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        
        # Diarize
        diarize_segments = diarize_model(audio)
        
        # Log the structure of diarize_segments
        logger.info(f"Diarize segments type: {type(diarize_segments)}")
        logger.info(f"Diarize segments columns: {diarize_segments.columns if isinstance(diarize_segments, pd.DataFrame) else 'Not a DataFrame'}")
        
        # Assign speaker labels to segments
        diarization_result = []
        for i, (segment, label) in enumerate(zip(vad_segments, labels)):
            whisperx_speaker = find_matching_whisperx_speaker(segment, diarize_segments)
            diarization_result.append({
                "start": segment[0],
                "end": segment[1],
                "speaker": f"Speaker_{label}",
                "whisperx_speaker": whisperx_speaker
            })
            
        logger.info(f"Diarization completed. Found {len(set(labels))} speakers.")
        return diarization_result
    except Exception as e:
        logger.error(f"Error during diarization: {str(e)}")
        raise
        
def find_matching_whisperx_speaker(segment, diarize_segments):
    if isinstance(diarize_segments, pd.DataFrame):
        matching_segments = diarize_segments[
            (diarize_segments['start'] <= segment[1]) & 
            (diarize_segments['end'] >= segment[0])
        ]
        if not matching_segments.empty:
            return matching_segments.iloc[0]['speaker']
    else:
        logger.warning("Unexpected type for diarize_segments. Expected DataFrame.")
    return "Unknown"

def find_matching_transcription(segment, transcription):
    for trans in transcription:
        if (trans['start'] <= segment[1] and trans["end"] >= segment[0]):
            return trans['text']
    return ""
