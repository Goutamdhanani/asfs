"""YouTube uploader using Data API v3."""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def upload_to_youtube(
    video_path: str,
    caption: str,
    hashtags: list,
    credentials: Dict
) -> Optional[str]:
    """
    Upload video to YouTube Shorts using Data API v3.
    
    Args:
        video_path: Path to video file
        caption: Video caption/description
        hashtags: List of hashtags
        credentials: YouTube API credentials (OAuth2)
        
    Returns:
        Video ID if successful, None if failed
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info("Uploading to YouTube Shorts")
    
    # Get credentials from environment or credentials dict
    credentials_file = credentials.get("credentials_file") or os.getenv("YOUTUBE_CREDENTIALS_FILE")
    
    if not credentials_file:
        logger.warning("YouTube credentials file not provided")
        logger.warning("Set YOUTUBE_CREDENTIALS_FILE environment variable")
    
    try:
        # Import Google API client
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # OAuth 2.0 scopes
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        # Authenticate
        creds = None
        
        # Check if we have stored credentials
        token_file = credentials.get("token_file") or os.getenv("YOUTUBE_TOKEN_FILE")
        
        if token_file and os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # If no valid credentials, need to authenticate
        if not creds or not creds.valid:
            if credentials_file and os.path.exists(credentials_file):
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                if token_file:
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
            else:
                logger.error("No YouTube credentials available")
                raise ValueError("YouTube credentials required")
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Prepare video metadata
        title = caption[:100] if len(caption) <= 100 else caption[:97] + "..."
        description = f"{caption}\n\n{' '.join(hashtags)}\n\n#Shorts"
        
        # Video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': [tag.replace('#', '') for tag in hashtags[:15]],  # Max 15 tags
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Create media upload
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        logger.info("Initiating YouTube upload")
        
        # Execute upload
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")
        
        video_id = response.get('id')
        
        logger.info(f"YouTube upload successful: {video_id}")
        logger.info(f"Video URL: https://youtube.com/shorts/{video_id}")
        
        return video_id
        
    except ImportError as e:
        logger.error(f"Required library not available: {str(e)}")
        logger.warning("YouTube upload skipped - install google-api-python-client google-auth-oauthlib")
        return None
    except Exception as e:
        logger.error(f"YouTube upload failed: {str(e)}")
        return None
