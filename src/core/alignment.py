import logging

logger = logging.getLogger(__name__)

def align_transcription_with_diarization(transcription, diarization_result):
    try:
        logger.info("Starting alignment of transcription with diarization results")
        logger.debug(f"Transcription segments: {len(transcription)}, Diarization segments: {len(diarization_result)}")
        
        aligned_transcript = []
        for i, trans_segment in enumerate(transcription):
            logger.debug(f"Processing transcription segment {i}: {trans_segment['start']:.2f}-{trans_segment['end']:.2f}")
            
            matching_diar_segments = [
                d for d in diarization_result
                if (d['start'] <= trans_segment['end'] and d['end'] >= trans_segment['start'])
            ]
            
            if matching_diar_segments:
                # Choose the diarization segment with the most overlap
                best_match = max(matching_diar_segments, key=lambda d: 
                                 min(d['end'], trans_segment['end']) - 
                                 max(d['start'], trans_segment['start']))
                
                overlap = min(best_match['end'], trans_segment['end']) - max(best_match['start'], trans_segment['start'])
                logger.debug(f"  Best match: Speaker {best_match['speaker']}, WhisperX: {best_match.get('whisperx_speaker', 'Unknown')}, overlap: {overlap:.2f}s")
                
                aligned_transcript.append({
                    "start": trans_segment['start'],
                    "end": trans_segment['end'],
                    "speaker": best_match['speaker'],
                    "whisperx_speaker": best_match.get('whisperx_speaker', 'Unknown'),
                    "text": trans_segment['text']
                })
            else:
                logger.warning(f"  No matching diarization segment for transcription {trans_segment['start']:.2f}-{trans_segment['end']:.2f}")
                aligned_transcript.append({
                    "start": trans_segment['start'],
                    "end": trans_segment['end'],
                    "speaker": "UNKNOWN",
                    "whisperx_speaker": "UNKNOWN",
                    "text": trans_segment['text']
                })
        
        logger.info("Alignment completed successfully")
        logger.debug(f"Aligned transcript has {len(aligned_transcript)} segments")
        return aligned_transcript
    except Exception as e:
        logger.error(f"Error during alignment: {str(e)}", exc_info=True)
        # In case of error, return the original transcription without speaker labels
        logger.warning("Returning original transcription without speaker labels due to alignment error")
        return [{"start": seg['start'], "end": seg['end'], "speaker": "UNKNOWN", "whisperx_speaker": "UNKNOWN", "text": seg['text']} for seg in transcription]