"""Candidate segment builders."""

from .sentence_window import build_sentence_windows
from .pause_window import build_pause_windows

__all__ = ['build_sentence_windows', 'build_pause_windows']
