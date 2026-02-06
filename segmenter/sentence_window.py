"""Sentence-based windowing for candidate segments."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def build_sentence_windows(
    transcript_data: Dict,
    min_duration: float = 10.0,
    max_duration: float = 75.0,
    overlap: float = 5.0
) -> List[Dict]:
    """
    Build candidate segments using sentence boundaries with overlapping windows.
    
    Args:
        transcript_data: Transcript dictionary from transcribe.py
        min_duration: Minimum segment duration in seconds
        max_duration: Maximum segment duration in seconds
        overlap: Overlap between windows in seconds
        
    Returns:
        List of candidate segment dictionaries with start, end, and text
    """
    segments = transcript_data.get("segments", [])
    
    if not segments:
        logger.warning("No segments in transcript")
        return []
    
    candidates = []
    
    # Iterate through segments to build windows
    i = 0
    while i < len(segments):
        window_start = segments[i]["start"]
        window_text = []
        j = i
        
        # Extend window until we reach max_duration or end of segments
        while j < len(segments):
            current_duration = segments[j]["end"] - window_start
            
            if current_duration > max_duration:
                break
            
            window_text.append(segments[j]["text"])
            
            # Check if we have a valid window (meets min_duration)
            if current_duration >= min_duration:
                candidate = {
                    "start": window_start,
                    "end": segments[j]["end"],
                    "duration": segments[j]["end"] - window_start,
                    "text": " ".join(window_text),
                    "segment_count": j - i + 1,
                    "type": "sentence_window"
                }
                candidates.append(candidate)
            
            j += 1
        
        # Move to next starting position with overlap
        # Find the segment that starts after window_start + (max_duration - overlap)
        next_start_time = window_start + max_duration - overlap
        
        i += 1
        while i < len(segments) and segments[i]["start"] < next_start_time:
            i += 1
        
        # Prevent infinite loop
        if i == j:
            i += 1
    
    logger.info(f"Built {len(candidates)} sentence-based candidate windows")
    
    # Log some statistics
    if candidates:
        avg_duration = sum(c["duration"] for c in candidates) / len(candidates)
        logger.info(f"Average candidate duration: {avg_duration:.1f}s")
    
    return candidates
