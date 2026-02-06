"""Video normalization using FFmpeg."""

import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def normalize_video(input_path: str, output_dir: str) -> str:
    """
    Normalize video to standard format for platform compatibility.
    
    Target specs:
    - Resolution: 1080x1920 (vertical)
    - Frame rate: 30 fps
    - Audio: 44100Hz stereo
    - Codec: H.264 + AAC
    
    Args:
        input_path: Path to input video file
        output_dir: Directory to save normalized video
        
    Returns:
        Path to normalized video file
        
    Raises:
        FileNotFoundError: If input video doesn't exist
        subprocess.CalledProcessError: If FFmpeg processing fails
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "normalized.mp4")
    
    logger.info(f"Normalizing video: {input_path}")
    logger.info(f"Output will be saved to: {output_path}")
    
    # FFmpeg command for normalization
    # -i: input file
    # -vf scale: resize and pad to 1080x1920 maintaining aspect ratio
    # -r: frame rate
    # -ar: audio sample rate
    # -ac: audio channels (stereo)
    # -c:v: video codec
    # -c:a: audio codec
    # -preset: encoding speed/quality tradeoff
    # -crf: quality (lower = better, 23 is default)
    # -y: overwrite output file
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',
        '-r', '30',
        '-ar', '44100',
        '-ac', '2',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-preset', 'medium',
        '-crf', '23',
        '-movflags', '+faststart',
        '-y',
        output_path
    ]
    
    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Video normalization completed successfully")
        logger.debug(f"FFmpeg output: {result.stderr}")
        
        # Verify output file was created
        if not os.path.exists(output_path):
            raise RuntimeError("Normalized video file was not created")
            
        file_size = os.path.getsize(output_path)
        logger.info(f"Normalized video size: {file_size / (1024*1024):.2f} MB")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg normalization failed: {e.stderr}")
        raise RuntimeError(f"Video normalization failed: {e.stderr}")
