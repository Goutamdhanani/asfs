"""Generate platform-specific captions."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Platform-specific caption length limits
CAPTION_LIMITS = {
    "TikTok": 2200,
    "Instagram": 2200,
    "YouTube": 5000
}


def generate_captions(clip: Dict, platforms: List[str] = None) -> Dict[str, str]:
    """
    Generate platform-optimized captions for a clip.
    
    Args:
        clip: Clip dictionary with AI analysis
        platforms: List of target platforms (defaults to all)
        
    Returns:
        Dictionary mapping platform names to captions
    """
    if platforms is None:
        platforms = ["TikTok", "Instagram", "YouTube"]
    
    captions = {}
    
    # Get AI-generated caption if available
    ai_analysis = clip.get("ai_analysis", {})
    base_caption = ai_analysis.get("caption", "")
    
    # Fallback to clip text if no AI caption
    if not base_caption:
        clip_text = clip.get("text", "")
        # Create a hook from first sentence
        sentences = clip_text.split(".")
        if sentences:
            base_caption = sentences[0].strip()[:150]
    
    # Get hashtags for inclusion
    hashtags = ai_analysis.get("hashtags", [])
    hashtag_text = " ".join(hashtags) if hashtags else ""
    
    for platform in platforms:
        limit = CAPTION_LIMITS.get(platform, 2200)
        
        # Build caption with call-to-action
        if platform == "TikTok":
            cta = "\n\n🔥 Follow for more! #fyp #foryou"
            caption = f"{base_caption}\n\n{hashtag_text}{cta}"
            
        elif platform == "Instagram":
            cta = "\n\n💡 Save this for later!\n👉 Follow for daily content"
            caption = f"{base_caption}\n\n{hashtag_text}{cta}"
            
        elif platform == "YouTube":
            cta = "\n\n🎯 Subscribe for more shorts!"
            caption = f"{base_caption}\n\n{hashtag_text}{cta}"
            
        else:
            caption = f"{base_caption}\n\n{hashtag_text}"
        
        # Truncate if exceeds limit
        if len(caption) > limit:
            # Remove hashtags if needed to fit
            caption = f"{base_caption}\n\n{cta}"[:limit]
        
        captions[platform] = caption
        
        logger.debug(f"Generated {platform} caption ({len(caption)} chars)")
    
    return captions


def truncate_caption(text: str, max_length: int) -> str:
    """
    Truncate caption to maximum length while preserving complete words.
    
    Args:
        text: Caption text
        max_length: Maximum length
        
    Returns:
        Truncated caption
    """
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + "..."
