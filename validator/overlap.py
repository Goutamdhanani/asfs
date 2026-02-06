"""Remove overlapping clips."""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def remove_overlapping_clips(
    clips: List[Dict],
    max_overlap: float = 5.0
) -> List[Dict]:
    """
    Remove clips with significant time overlap.
    
    Args:
        clips: List of clip dictionaries with start and end times
        max_overlap: Maximum allowed overlap in seconds
        
    Returns:
        List of non-overlapping clips (keeps higher-scored clips)
    """
    if not clips:
        return []
    
    # Sort clips by score (highest first) to prioritize better clips
    sorted_clips = sorted(
        clips,
        key=lambda x: x.get("overall_score", 0),
        reverse=True
    )
    
    validated_clips = []
    
    for clip in sorted_clips:
        clip_start = clip["start"]
        clip_end = clip["end"]
        
        # Check overlap with already validated clips
        has_significant_overlap = False
        
        for validated in validated_clips:
            val_start = validated["start"]
            val_end = validated["end"]
            
            # Calculate overlap
            overlap_start = max(clip_start, val_start)
            overlap_end = min(clip_end, val_end)
            overlap_duration = max(0, overlap_end - overlap_start)
            
            if overlap_duration > max_overlap:
                has_significant_overlap = True
                logger.debug(f"Clip ({clip_start:.1f}s-{clip_end:.1f}s) overlaps "
                           f"{overlap_duration:.1f}s with validated clip "
                           f"({val_start:.1f}s-{val_end:.1f}s)")
                break
        
        if not has_significant_overlap:
            validated_clips.append(clip)
    
    # Sort back by start time for chronological order
    validated_clips.sort(key=lambda x: x["start"])
    
    removed_count = len(clips) - len(validated_clips)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} overlapping clips")
    
    logger.info(f"Validated {len(validated_clips)} non-overlapping clips")
    
    return validated_clips
