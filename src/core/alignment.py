import logging

logger = logging.getLogger(__name__)

def align_transcription_with_diarization(transcription, diarization_result):
    try:
        logger.info("Starting alignment of transcription with diarization results")
        
        aligned_transcript = []
        for trans_segment in transcription:
            matching_diar_segments = [
                d for d in diarization_result
                if (d['start'] <= trans_segment['end'] and d['end'] >= trans_segment['start'])
            ]
            
            if matching_diar_segments:
                # Choose the diarization segment with the most overlap
                best_match = max(matching_diar_segments, key=lambda d: 
                                 min(d['end'], trans_segment['end']) - 
                                 max(d['start'], trans_segment['start']))
                
                aligned_transcript.append({
                    "start": trans_segment['start'],
                    "end": trans_segment['end'],
                    "speaker": best_match['speaker'],
                    "text": trans_segment['text']
                })
            else:
                # If no matching diarization segment, keep the transcription as is
                aligned_transcript.append({
                    "start": trans_segment['start'],
                    "end": trans_segment['end'],
                    "speaker": "UNKNOWN",
                    "text": trans_segment['text']
                })
        
        logger.info("Alignment completed successfully")
        return aligned_transcript
    except Exception as e:
        logger.error(f"Error during alignment: {str(e)}")
        raise