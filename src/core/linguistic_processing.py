import logging
import re

logger = logging.getLogger(__name__)

def linguistic_post_processing(segments):
    """
    Apply conservative linguistic post-processing to refine speaker diarization results.
    This function looks for clear question-answer patterns and adjusts speaker labels
    only when there's high confidence in the change.
    """
    logger.info("Starting conservative linguistic post-processing")
    for i in range(len(segments) - 1):
        current_segment = segments[i]
        next_segment = segments[i + 1]
        
        # Check if the current segment ends with a question mark and is short
        if current_segment['text'].strip().endswith('?') and len(current_segment['text'].split()) <= 10:
            logger.debug(f"Short question detected: {current_segment['text']}")
            
            # Check if the next segment is a likely answer (short and doesn't end with a question)
            if len(next_segment['text'].split()) <= 15 and not next_segment['text'].strip().endswith('?'):
                # If the next segment has the same speaker, consider changing it
                if current_segment['speaker'] == next_segment['speaker']:
                    current_speaker_num = int(re.search(r'\d+', current_segment['speaker']).group())
                    new_speaker_num = (current_speaker_num % 2) + 1
                    next_segment['speaker'] = f"SPEAKER_{new_speaker_num:02d}"
                    logger.debug(f"Changed speaker for likely answer: {next_segment['text']}")
    
    logger.info("Conservative linguistic post-processing completed")
    return segments