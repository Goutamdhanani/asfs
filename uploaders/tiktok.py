"""TikTok uploader using Content Posting API."""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def upload_to_tiktok(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: Dict
) -> Optional[str]:
    """
    Upload video to TikTok using Content Posting API.
    
    Args:
        video_path: Path to video file
        caption: Video caption
        hashtags: List of hashtags
        credentials: TikTok API credentials (access_token, etc.)
        
    Returns:
        Upload ID if successful, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Uploading to TikTok")
    
    # Get credentials
    access_token = credentials.get("access_token") or os.getenv("TIKTOK_ACCESS_TOKEN")
    
    if not access_token:
        logger.error("TikTok access token not provided")
        raise ValueError("TikTok access token required. Set TIKTOK_ACCESS_TOKEN environment variable.")
    
    try:
        # Import TikTok SDK or use requests
        import requests
        
        # TikTok Content Posting API endpoint
        # Note: This requires TikTok for Developers account and OAuth2 flow
        endpoint = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
        # Prepare caption with hashtags
        full_caption = f"{caption}\n\n{' '.join(hashtags)}"
        
        # Get video file size
        file_size = os.path.getsize(video_path)
        
        # Initialize upload
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        init_data = {
            "post_info": {
                "title": full_caption[:150],  # TikTok title limit
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
        
        logger.info("Initializing TikTok upload")
        response = requests.post(endpoint, headers=headers, json=init_data)
        
        if response.status_code != 200:
            logger.error(f"TikTok upload init failed: {response.status_code} {response.text}")
            return None
        
        result = response.json()
        
        if result.get("error"):
            error = result["error"]
            logger.error(f"TikTok API error: {error.get('code')} - {error.get('message')}")
            return None
        
        data = result.get("data", {})
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")
        
        if not upload_url:
            logger.error("No upload URL received from TikTok")
            return None
        
        # Upload video file
        logger.info("Uploading video file to TikTok")
        
        with open(video_path, 'rb') as video_file:
            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size)
            }
            
            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=video_file
            )
            
            if upload_response.status_code not in [200, 201]:
                logger.error(f"TikTok video upload failed: {upload_response.status_code}")
                return None
        
        logger.info(f"TikTok upload successful: {publish_id}")
        return publish_id
        
    except ImportError:
        logger.error("requests library not available")
        logger.warning("TikTok upload skipped - install requests library")
        return None
    except Exception as e:
        logger.error(f"TikTok upload failed: {str(e)}")
        return None
