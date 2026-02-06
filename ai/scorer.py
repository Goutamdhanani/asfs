"""AI highlight scoring using GitHub Models API."""

import os
import json
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing Azure AI Inference SDK
try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logger.warning("Azure AI Inference SDK not available, will try OpenAI SDK")

# Fallback to OpenAI SDK
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


def load_prompt_template() -> str:
    """Load the scoring prompt template."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def score_segments(
    candidates: List[Dict],
    model_config: Dict,
    max_segments: int = 50
) -> List[Dict]:
    """
    Score candidate segments using GitHub Models API.
    
    Args:
        candidates: List of candidate segment dictionaries
        model_config: Model configuration (endpoint, model_name, api_key)
        max_segments: Maximum number of segments to score (top candidates first)
        
    Returns:
        List of scored segments with AI analysis
    """
    if not candidates:
        logger.warning("No candidate segments to score")
        return []
    
    # Get API credentials from config or environment
    endpoint = model_config.get("endpoint") or os.getenv("GITHUB_MODELS_ENDPOINT")
    api_key = model_config.get("api_key") or os.getenv("GITHUB_TOKEN")
    model_name = model_config.get("model_name", "gpt-4o")
    
    if not endpoint:
        endpoint = "https://models.inference.ai.azure.com"
    
    if not api_key:
        raise ValueError("GitHub API token not provided. Set GITHUB_TOKEN environment variable.")
    
    logger.info(f"Scoring {min(len(candidates), max_segments)} segments using {model_name}")
    
    # Load prompt template
    prompt_template = load_prompt_template()
    
    # Limit to max_segments (score best candidates based on duration and position)
    segments_to_score = candidates[:max_segments] if len(candidates) > max_segments else candidates
    
    scored_segments = []
    
    # Initialize AI client
    client = None
    
    if AZURE_SDK_AVAILABLE:
        try:
            client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            logger.info("Using Azure AI Inference SDK")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure SDK: {e}")
    
    if client is None and OPENAI_SDK_AVAILABLE:
        try:
            client = OpenAI(
                base_url=endpoint,
                api_key=api_key
            )
            logger.info("Using OpenAI SDK")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI SDK: {e}")
    
    if client is None:
        raise RuntimeError("No compatible SDK available. Install azure-ai-inference or openai.")
    
    for idx, segment in enumerate(segments_to_score):
        try:
            # Format prompt with segment data
            prompt = prompt_template.format(
                segment_text=segment["text"],
                duration=f"{segment['duration']:.1f}"
            )
            
            # Call AI model
            if AZURE_SDK_AVAILABLE and isinstance(client, ChatCompletionsClient):
                response = client.complete(
                    messages=[
                        {"role": "system", "content": "You are a video content analyzer. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model_name,
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                
            else:  # OpenAI SDK
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a video content analyzer. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
            
            # Parse AI response
            try:
                # Clean up response (remove markdown code blocks if present)
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].split("```")[0].strip()
                
                ai_analysis = json.loads(ai_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response was: {ai_response}")
                # Create default analysis
                ai_analysis = {
                    "scores": {
                        "hook_strength": 5,
                        "emotional_resonance": 5,
                        "clarity": 5,
                        "virality_potential": 5,
                        "platform_fit": 5
                    },
                    "overall_score": 5.0,
                    "recommendation": "AVERAGE",
                    "caption": segment["text"][:100],
                    "hashtags": ["#viral", "#shorts"],
                    "best_platforms": ["TikTok", "Instagram", "YouTube"],
                    "reasoning": "AI analysis failed, using default scores"
                }
            
            # Combine segment data with AI analysis
            scored_segment = {
                **segment,
                "ai_analysis": ai_analysis,
                "overall_score": ai_analysis.get("overall_score", 5.0)
            }
            
            scored_segments.append(scored_segment)
            
            logger.info(f"Scored segment {idx + 1}/{len(segments_to_score)}: "
                       f"{ai_analysis.get('overall_score', 0):.1f}/10 "
                       f"({ai_analysis.get('recommendation', 'UNKNOWN')})")
            
        except Exception as e:
            logger.error(f"Failed to score segment {idx + 1}: {str(e)}")
            # Add segment without AI score
            scored_segments.append({
                **segment,
                "ai_analysis": {
                    "error": str(e),
                    "overall_score": 0.0
                },
                "overall_score": 0.0
            })
    
    # Sort by overall score (highest first)
    scored_segments.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    
    logger.info(f"Completed scoring {len(scored_segments)} segments")
    
    if scored_segments:
        top_score = scored_segments[0].get("overall_score", 0)
        logger.info(f"Top segment score: {top_score:.1f}/10")
    
    return scored_segments
