"""Video transcription using Whisper."""

import os
import json
import logging
import whisper
from typing import List, Dict

logger = logging.getLogger(__name__)


def transcribe_video(video_path: str, output_dir: str, model_size: str = "base") -> str:
    """
    Transcribe video using OpenAI Whisper with sentence-level timestamps.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save transcript JSON
        model_size: Whisper model size (tiny, base, small, medium, large)
        
    Returns:
        Path to transcript JSON file
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        RuntimeError: If transcription fails
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "transcript.json")
    
    logger.info(f"Loading Whisper model: {model_size}")
    
    try:
        model = whisper.load_model(model_size)
        logger.info(f"Transcribing video: {video_path}")
        
        # Transcribe with word-level timestamps
        result = model.transcribe(
            video_path,
            word_timestamps=True,
            verbose=False
        )
        
        # Extract structured transcript data
        transcript_data = {
            "language": result.get("language", "unknown"),
            "language_probability": result.get("language_probability", 0.0),
            "duration": result.get("duration", 0.0),
            "segments": []
        }
        
        # Convert segments to our format
        for segment in result.get("segments", []):
            segment_data = {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": []
            }
            
            # Include word-level data if available
            if "words" in segment:
                for word in segment["words"]:
                    segment_data["words"].append({
                        "word": word.get("word", "").strip(),
                        "start": word.get("start", 0.0),
                        "end": word.get("end", 0.0),
                        "probability": word.get("probability", 0.0)
                    })
            
            transcript_data["segments"].append(segment_data)
        
        # Save transcript to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Transcription completed: {len(transcript_data['segments'])} segments")
        logger.info(f"Language detected: {transcript_data['language']} "
                   f"(confidence: {transcript_data['language_probability']:.2f})")
        logger.info(f"Transcript saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise RuntimeError(f"Failed to transcribe video: {str(e)}")


def load_transcript(transcript_path: str) -> Dict:
    """
    Load transcript from JSON file.
    
    Args:
        transcript_path: Path to transcript JSON
        
    Returns:
        Transcript data dictionary
    """
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        return json.load(f)
