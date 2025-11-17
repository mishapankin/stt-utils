__all__ = [
    "Transcription",
    "UnprocessedTranscription",
    "UnprocessedTimestamp",
    "Timestamp",
    "normalize_word",
    "split_audio_on_silence",
]

from .transcription import (
    Transcription,
    UnprocessedTranscription,
    UnprocessedTimestamp,
    Timestamp,
    normalize_word,
)


def __getattr__(name):
    if name == "split_audio_on_silence":
        try:
            from .splitter import split_audio_on_silence

            return split_audio_on_silence
        except ImportError as e:
            raise e
    raise AttributeError(f"module 'stt_utils' has no attribute '{name}'")
