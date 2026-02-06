"""Clip validation and deduplication."""

from .dedup import deduplicate_clips
from .overlap import remove_overlapping_clips

__all__ = ['deduplicate_clips', 'remove_overlapping_clips']
