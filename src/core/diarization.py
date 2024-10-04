import logging
import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
from src import config

logger = logging.getLogger(__name__)

def apply_diarization(vad_segments, embeddings):
    try:
        logger.info("Starting speaker diarization")
        
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
        
        # Assign speaker labels to segments
        diarization_result = []
        for i, (segment, label) in enumerate(zip(vad_segments, labels)):
            diarization_result.append({
                "start": segment[0],
                "end": segment[1],
                "speaker": f"Speaker_{label}"
            })
            
        logger.info(f"Diarization completed. Found {len(set(labels))} speakers.")
        return diarization_result
    except Exception as e:
        logger.error(f"Error during diarization: {str(e)}")
        raise
        