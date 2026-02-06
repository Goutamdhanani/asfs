"""Pause-based windowing for candidate segments."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def build_pause_windows(
    transcript_data: Dict,
    min_duration: float = 10.0,
    max_duration: float = 75.0,
    min_pause: float = 0.5
) -> List[Dict]:
    """
    Build candidate segments using natural pauses in speech.
    
    Args:
        transcript_data: Transcript dictionary from transcribe.py
        min_duration: Minimum segment duration in seconds
        max_duration: Maximum segment duration in seconds
        min_pause: Minimum pause duration to consider as boundary (seconds)
        
    Returns:
        List of candidate segment dictionaries with start, end, and text
    """
    segments = transcript_data.get("segments", [])
    
    if not segments:
        logger.warning("No segments in transcript")
        return []
    
    # Find pauses between segments
    pauses = []
    
    for i in range(len(segments) - 1):
        current_end = segments[i]["end"]
        next_start = segments[i + 1]["start"]
        pause_duration = next_start - current_end
        
        if pause_duration >= min_pause:
            pauses.append({
                "time": current_end,
                "duration": pause_duration,
                "after_segment": i
            })
    
    logger.info(f"Found {len(pauses)} pauses >= {min_pause}s")
    
    candidates = []
    
    # Build segments between pauses
    segment_start_idx = 0
    
    for pause in pauses:
        segment_end_idx = pause["after_segment"]
        
        # Calculate duration of this segment
        if segment_start_idx < len(segments) and segment_end_idx < len(segments):
            start_time = segments[segment_start_idx]["start"]
            end_time = segments[segment_end_idx]["end"]
            duration = end_time - start_time
            
            # Check if segment meets duration criteria
            if min_duration <= duration <= max_duration:
                # Collect text from all segments in this window
                text_parts = []
                for idx in range(segment_start_idx, segment_end_idx + 1):
                    text_parts.append(segments[idx]["text"])
                
                candidate = {
                    "start": start_time,
                    "end": end_time,
                    "duration": duration,
                    "text": " ".join(text_parts),
                    "segment_count": segment_end_idx - segment_start_idx + 1,
                    "type": "pause_window",
                    "pause_after": pause["duration"]
                }
                candidates.append(candidate)
            
            elif duration > max_duration:
                # Split long segments at natural pauses
                current_start_idx = segment_start_idx
                
                for idx in range(segment_start_idx, segment_end_idx + 1):
                    current_start = segments[current_start_idx]["start"]
                    current_end = segments[idx]["end"]
                    current_duration = current_end - current_start
                    
                    if current_duration >= min_duration:
                        # Check if adding next segment would exceed max_duration
                        if idx + 1 <= segment_end_idx:
                            next_duration = segments[idx + 1]["end"] - current_start
                            if next_duration > max_duration:
                                # Create candidate here
                                text_parts = []
                                for text_idx in range(current_start_idx, idx + 1):
                                    text_parts.append(segments[text_idx]["text"])
                                
                                candidate = {
                                    "start": current_start,
                                    "end": current_end,
                                    "duration": current_duration,
                                    "text": " ".join(text_parts),
                                    "segment_count": idx - current_start_idx + 1,
                                    "type": "pause_window_split"
                                }
                                candidates.append(candidate)
                                current_start_idx = idx + 1
        
        # Move to next segment after pause
        segment_start_idx = segment_end_idx + 1
    
    # Handle remaining segments after last pause
    if segment_start_idx < len(segments):
        start_time = segments[segment_start_idx]["start"]
        end_time = segments[-1]["end"]
        duration = end_time - start_time
        
        if min_duration <= duration <= max_duration:
            text_parts = []
            for idx in range(segment_start_idx, len(segments)):
                text_parts.append(segments[idx]["text"])
            
            candidate = {
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "text": " ".join(text_parts),
                "segment_count": len(segments) - segment_start_idx,
                "type": "pause_window_final"
            }
            candidates.append(candidate)
    
    logger.info(f"Built {len(candidates)} pause-based candidate windows")
    
    return candidates
