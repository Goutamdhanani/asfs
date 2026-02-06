"""Transcript quality validation."""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def check_transcript_quality(transcript_data: Dict) -> Tuple[float, bool, Dict]:
    """
    Validate transcript quality before processing.
    
    Checks:
    - Timestamp continuity (no major gaps or overlaps)
    - Word density (words per second)
    - Filler word percentage
    - Language confidence
    
    Args:
        transcript_data: Transcript dictionary from transcribe.py
        
    Returns:
        Tuple of (quality_score, passed, details_dict)
        - quality_score: 0.0 to 1.0
        - passed: True if transcript meets minimum quality
        - details_dict: Detailed quality metrics
    """
    segments = transcript_data.get("segments", [])
    
    if not segments:
        logger.warning("No segments found in transcript")
        return 0.0, False, {"error": "No segments found"}
    
    # Initialize quality metrics
    quality_metrics = {
        "timestamp_continuity": 0.0,
        "word_density": 0.0,
        "filler_percentage": 0.0,
        "language_confidence": transcript_data.get("language_probability", 0.0),
        "total_segments": len(segments),
        "issues": []
    }
    
    # 1. Check timestamp continuity
    gaps = []
    overlaps = []
    
    for i in range(len(segments) - 1):
        current_end = segments[i]["end"]
        next_start = segments[i + 1]["start"]
        
        gap = next_start - current_end
        
        if gap > 5.0:  # Gap larger than 5 seconds
            gaps.append(gap)
        elif gap < -0.5:  # Overlap more than 0.5 seconds
            overlaps.append(abs(gap))
    
    # Score timestamp continuity
    total_transitions = len(segments) - 1
    if total_transitions > 0:
        problematic_transitions = len(gaps) + len(overlaps)
        continuity_score = 1.0 - (problematic_transitions / total_transitions)
        quality_metrics["timestamp_continuity"] = max(0.0, continuity_score)
        quality_metrics["gaps_count"] = len(gaps)
        quality_metrics["overlaps_count"] = len(overlaps)
    else:
        quality_metrics["timestamp_continuity"] = 1.0
    
    # 2. Check word density (words per second)
    total_words = 0
    total_duration = 0.0
    
    for segment in segments:
        text = segment.get("text", "")
        words = text.split()
        total_words += len(words)
        
        duration = segment["end"] - segment["start"]
        total_duration += duration
    
    if total_duration > 0:
        words_per_second = total_words / total_duration
        quality_metrics["words_per_second"] = words_per_second
        
        # Typical speech is 2-3 words per second
        # Score based on how close to normal range
        if 1.5 <= words_per_second <= 4.0:
            density_score = 1.0
        elif words_per_second < 0.5:
            density_score = 0.0  # Too sparse, likely bad transcription
        elif words_per_second > 6.0:
            density_score = 0.5  # Very fast, might be overlapping audio
        else:
            # Gradual falloff for slightly abnormal rates
            density_score = 0.7
        
        quality_metrics["word_density"] = density_score
    else:
        quality_metrics["word_density"] = 0.0
        quality_metrics["words_per_second"] = 0.0
    
    # 3. Check filler word percentage
    filler_words = {
        "um", "uh", "er", "ah", "like", "you know", "i mean",
        "actually", "basically", "literally", "so", "well"
    }
    
    filler_count = 0
    
    for segment in segments:
        text = segment.get("text", "").lower()
        words = text.split()
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?;:')
            if clean_word in filler_words:
                filler_count += 1
    
    if total_words > 0:
        filler_percentage = (filler_count / total_words) * 100
        quality_metrics["filler_percentage"] = filler_percentage
        
        # Lower is better for fillers
        if filler_percentage < 5.0:
            filler_score = 1.0
        elif filler_percentage > 20.0:
            filler_score = 0.5  # Very high filler rate
        else:
            filler_score = 1.0 - ((filler_percentage - 5.0) / 15.0) * 0.5
    else:
        filler_score = 0.0
        quality_metrics["filler_percentage"] = 0.0
    
    # 4. Language confidence score
    lang_confidence = quality_metrics["language_confidence"]
    
    if lang_confidence < 0.5:
        quality_metrics["issues"].append("Low language confidence")
    
    # Calculate overall quality score (weighted average)
    weights = {
        "timestamp_continuity": 0.3,
        "word_density": 0.3,
        "filler_score": 0.2,
        "language_confidence": 0.2
    }
    
    overall_score = (
        weights["timestamp_continuity"] * quality_metrics["timestamp_continuity"] +
        weights["word_density"] * quality_metrics["word_density"] +
        weights["filler_score"] * filler_score +
        weights["language_confidence"] * lang_confidence
    )
    
    quality_metrics["overall_score"] = overall_score
    
    # Determine pass/fail (threshold: 0.6)
    passed = overall_score >= 0.6
    
    # Add specific issues
    if quality_metrics["timestamp_continuity"] < 0.7:
        quality_metrics["issues"].append("Timestamp continuity issues detected")
    
    if quality_metrics.get("words_per_second", 0) < 1.0:
        quality_metrics["issues"].append("Word density too low")
    elif quality_metrics.get("words_per_second", 0) > 5.0:
        quality_metrics["issues"].append("Word density too high")
    
    if filler_percentage > 15.0:
        quality_metrics["issues"].append("High filler word percentage")
    
    # Log results
    logger.info(f"Transcript quality score: {overall_score:.2f}")
    logger.info(f"Quality check: {'PASSED' if passed else 'FAILED'}")
    
    if quality_metrics["issues"]:
        logger.warning(f"Quality issues: {', '.join(quality_metrics['issues'])}")
    
    return overall_score, passed, quality_metrics
