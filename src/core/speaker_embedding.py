import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
import logging
from src import config
import numpy as np

logger = logging.getLogger(__name__)

def extract_speaker_embeddings(vad_segments):
    try:
        if not vad_segments:
            logger.error("Empty list of VAD segments provided")
            raise ValueError("VAD segments list is empty")
        
        logger.info("Loading SpeechBrain ECAPA-TDNN model for speaker embedding")
        classifier = EncoderClassifier.from_hparams(source=config.SPEAKER_EMBEDDING_MODEL)
        
        embeddings = []
        for i, segment in enumerate(vad_segments):
            # Ensure the segment is a 1D numpy array
            if isinstance(segment, np.ndarray) and segment.ndim == 1:
                waveform = torch.tensor(segment).unsqueeze(0)
            else:
                logger.warning(f"Skipping invalid segment at index {i}")
                continue
            
            # Ensure the waveform is long enough (at least 1 second)
            if waveform.shape[1] < config.SAMPLE_RATE:
                logger.warning(f"Padding short segment at index {i}")
                waveform = torch.nn.functional.pad(waveform, (0, config.SAMPLE_RATE - waveform.shape[1]))
            
            embedding = classifier.encode_batch(waveform)
            embeddings.append(embedding.squeeze().numpy())
            
            if i % 10 == 0:
                logger.info(f"Processed {i+1}/{len(vad_segments)} segments")
        
        embeddings = np.array(embeddings)
        logger.info(f"Speaker embeddings extracted successfully. Shape: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Speaker embedding extraction failed: {str(e)}")
        raise