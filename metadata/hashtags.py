"""Generate platform-specific hashtags."""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

# Platform-specific hashtag limits
HASHTAG_LIMITS = {
    "TikTok": 30,
    "Instagram": 30,
    "YouTube": 15
}

# Common broad hashtags for reach
BROAD_HASHTAGS = {
    "TikTok": ["#fyp", "#foryou", "#viral", "#trending"],
    "Instagram": ["#reels", "#reelsinstagram", "#viral", "#explore"],
    "YouTube": ["#shorts", "#youtubeshorts", "#viral"]
}


def generate_hashtags(
    clip: Dict,
    platforms: List[str] = None,
    max_hashtags: int = 10
) -> Dict[str, List[str]]:
    """
    Generate platform-optimized hashtags for a clip.
    
    Args:
        clip: Clip dictionary with AI analysis
        platforms: List of target platforms (defaults to all)
        max_hashtags: Maximum number of hashtags per platform
        
    Returns:
        Dictionary mapping platform names to hashtag lists
    """
    if platforms is None:
        platforms = ["TikTok", "Instagram", "YouTube"]
    
    hashtags_by_platform = {}
    
    # Get AI-generated hashtags if available
    ai_analysis = clip.get("ai_analysis", {})
    ai_hashtags = ai_analysis.get("hashtags", [])
    
    # Clean and normalize AI hashtags
    niche_hashtags = []
    for tag in ai_hashtags:
        # Ensure hashtag format
        if not tag.startswith("#"):
            tag = f"#{tag}"
        # Remove spaces
        tag = tag.replace(" ", "")
        niche_hashtags.append(tag.lower())
    
    # Deduplicate
    niche_hashtags = list(dict.fromkeys(niche_hashtags))
    
    for platform in platforms:
        platform_limit = min(
            HASHTAG_LIMITS.get(platform, 30),
            max_hashtags
        )
        
        # Start with platform-specific broad hashtags
        broad = BROAD_HASHTAGS.get(platform, [])
        
        # Combine broad + niche hashtags
        hashtags = broad.copy()
        
        # Add niche hashtags up to limit
        for tag in niche_hashtags:
            if len(hashtags) >= platform_limit:
                break
            if tag not in hashtags:
                hashtags.append(tag)
        
        # If we still need more hashtags, add generic ones
        if len(hashtags) < 5:
            generic = ["#content", "#video", "#viral", "#trending", "#fyp"]
            for tag in generic:
                if len(hashtags) >= platform_limit:
                    break
                if tag not in hashtags:
                    hashtags.append(tag)
        
        hashtags_by_platform[platform] = hashtags[:platform_limit]
        
        logger.debug(f"Generated {len(hashtags_by_platform[platform])} hashtags for {platform}")
    
    return hashtags_by_platform


def extract_keywords_from_text(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract potential hashtag keywords from text.
    
    Args:
        text: Clip text
        max_keywords: Maximum keywords to extract
        
    Returns:
        List of keyword strings
    """
    # Simple keyword extraction (can be enhanced with NLP)
    words = text.lower().split()
    
    # Filter out common words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "is", "was",
        "are", "were", "be", "been", "being", "have", "has", "had"
    }
    
    keywords = []
    for word in words:
        # Clean word
        clean_word = word.strip('.,!?;:"\'-')
        
        # Skip if too short, too long, or stop word
        if len(clean_word) < 3 or len(clean_word) > 20:
            continue
        if clean_word in stop_words:
            continue
        
        if clean_word not in keywords:
            keywords.append(clean_word)
        
        if len(keywords) >= max_keywords:
            break
    
    return keywords
