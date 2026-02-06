"""Semantic deduplication of clips."""

import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    # Normalize texts
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def deduplicate_clips(
    clips: List[Dict],
    similarity_threshold: float = 0.7
) -> List[Dict]:
    """
    Remove semantically similar clips based on text similarity.
    
    Args:
        clips: List of clip dictionaries with text field
        similarity_threshold: Minimum similarity to consider duplicates (0.0-1.0)
        
    Returns:
        List of unique clips (keeps higher-scored clips)
    """
    if not clips:
        return []
    
    if len(clips) == 1:
        return clips
    
    # Sort clips by score (highest first)
    sorted_clips = sorted(
        clips,
        key=lambda x: x.get("overall_score", 0),
        reverse=True
    )
    
    unique_clips = []
    
    for clip in sorted_clips:
        clip_text = clip.get("text", "")
        
        # Check similarity with already selected clips
        is_duplicate = False
        
        for unique in unique_clips:
            unique_text = unique.get("text", "")
            
            similarity = calculate_jaccard_similarity(clip_text, unique_text)
            
            if similarity >= similarity_threshold:
                is_duplicate = True
                logger.debug(f"Clip is {similarity:.2f} similar to existing clip, marking as duplicate")
                break
        
        if not is_duplicate:
            unique_clips.append(clip)
    
    removed_count = len(clips) - len(unique_clips)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} duplicate clips")
    
    logger.info(f"Retained {len(unique_clips)} unique clips")
    
    return unique_clips
