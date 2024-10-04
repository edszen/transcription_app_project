import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
import logging
from src import config
import numpy as np

logger = logging.getLogger(__name__)

def extract_speaker_embeddings(vad_segments):
    try:
        logger.info("Loading SpeechBrain ECAPA-TDNN model for speaker embedding")
        classifier = EncoderClassifier.from_hparams(source=config.SPEAKER_EMBEDDING_MODEL)
        
        embeddings = []
        for i, segment in enumerate(vad_segments):
            waveform = torch.tensor(segment).unsqueeze(0)
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