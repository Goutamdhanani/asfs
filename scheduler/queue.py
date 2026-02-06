"""Upload queue with rate limiting and retry logic."""

import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class UploadQueue:
    """
    Manages upload queue with rate limiting and retry logic.
    """
    
    def __init__(self, rate_limits_config: Dict):
        """
        Initialize upload queue.
        
        Args:
            rate_limits_config: Rate limit configuration dictionary
        """
        self.rate_limits = rate_limits_config
        self.last_upload_time = {}  # platform -> timestamp
        self.retry_counts = {}  # clip_id -> retry_count
        self.failed_uploads = []
        
        # Initialize last upload time for each platform
        for platform in self.rate_limits.keys():
            self.last_upload_time[platform] = None
    
    def can_upload(self, platform: str) -> bool:
        """
        Check if upload is allowed based on rate limits.
        
        Args:
            platform: Platform name
            
        Returns:
            True if upload is allowed
        """
        if platform not in self.rate_limits:
            logger.warning(f"No rate limits configured for {platform}")
            return True
        
        limits = self.rate_limits[platform]
        cooldown = limits.get("cooldown_seconds", 3600)
        
        last_upload = self.last_upload_time.get(platform)
        
        if last_upload is None:
            return True
        
        time_since_last = time.time() - last_upload
        
        if time_since_last < cooldown:
            wait_time = cooldown - time_since_last
            logger.info(f"Rate limit for {platform}: wait {wait_time:.0f}s")
            return False
        
        return True
    
    def wait_for_availability(self, platform: str, timeout: int = 3600):
        """
        Wait until upload is allowed for platform.
        
        Args:
            platform: Platform name
            timeout: Maximum wait time in seconds
        """
        start_time = time.time()
        
        while not self.can_upload(platform):
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for {platform} availability")
            
            limits = self.rate_limits[platform]
            cooldown = limits.get("cooldown_seconds", 3600)
            last_upload = self.last_upload_time.get(platform)
            
            if last_upload:
                wait_time = cooldown - (time.time() - last_upload)
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.0f}s for {platform}")
                    time.sleep(min(wait_time, 60))  # Check every minute
    
    def record_upload(self, platform: str, clip_id: str, success: bool):
        """
        Record upload attempt.
        
        Args:
            platform: Platform name
            clip_id: Clip identifier
            success: Whether upload succeeded
        """
        if success:
            self.last_upload_time[platform] = time.time()
            logger.info(f"Recorded successful upload to {platform} for {clip_id}")
            
            # Reset retry count on success
            if clip_id in self.retry_counts:
                del self.retry_counts[clip_id]
        else:
            # Increment retry count
            self.retry_counts[clip_id] = self.retry_counts.get(clip_id, 0) + 1
            
            self.failed_uploads.append({
                "clip_id": clip_id,
                "platform": platform,
                "timestamp": time.time(),
                "retry_count": self.retry_counts[clip_id]
            })
            
            logger.warning(f"Upload failed for {clip_id} to {platform} "
                         f"(attempt {self.retry_counts[clip_id]})")
    
    def should_retry(self, clip_id: str, max_retries: int = 3) -> bool:
        """
        Check if clip should be retried.
        
        Args:
            clip_id: Clip identifier
            max_retries: Maximum retry attempts
            
        Returns:
            True if should retry
        """
        retry_count = self.retry_counts.get(clip_id, 0)
        return retry_count < max_retries
    
    def get_backoff_delay(self, clip_id: str, base_delay: int = 300) -> int:
        """
        Calculate exponential backoff delay.
        
        Args:
            clip_id: Clip identifier
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds
        """
        retry_count = self.retry_counts.get(clip_id, 0)
        return base_delay * (2 ** retry_count)
    
    def schedule_clips(
        self,
        clips: List[Dict],
        platforms: List[str]
    ) -> List[Dict]:
        """
        Schedule clips for upload across platforms.
        
        Args:
            clips: List of clip dictionaries
            platforms: List of target platforms
            
        Returns:
            List of scheduled upload tasks
        """
        scheduled_tasks = []
        
        for clip in clips:
            clip_id = clip.get("clip_id", "unknown")
            
            # Determine best platforms for this clip
            ai_analysis = clip.get("ai_analysis", {})
            recommended_platforms = ai_analysis.get("best_platforms", platforms)
            
            # Filter to only platforms we support
            target_platforms = [p for p in recommended_platforms if p in platforms]
            
            # If no recommendations, use all platforms
            if not target_platforms:
                target_platforms = platforms
            
            for platform in target_platforms:
                task = {
                    "clip_id": clip_id,
                    "clip": clip,
                    "platform": platform,
                    "scheduled_time": None,  # Will be set when uploaded
                    "status": "pending"
                }
                scheduled_tasks.append(task)
        
        logger.info(f"Scheduled {len(scheduled_tasks)} upload tasks "
                   f"for {len(clips)} clips across {len(platforms)} platforms")
        
        return scheduled_tasks


def load_rate_limits(config_path: str) -> Dict:
    """
    Load rate limits from configuration file.
    
    Args:
        config_path: Path to rate_limits.json
        
    Returns:
        Rate limits dictionary
    """
    if not Path(config_path).exists():
        logger.warning(f"Rate limits config not found: {config_path}")
        # Return default rate limits
        return {
            "TikTok": {
                "cooldown_seconds": 3600,
                "max_per_day": 10
            },
            "Instagram": {
                "cooldown_seconds": 3600,
                "max_per_day": 10
            },
            "YouTube": {
                "cooldown_seconds": 3600,
                "max_per_day": 10
            }
        }
    
    with open(config_path, 'r') as f:
        return json.load(f)
