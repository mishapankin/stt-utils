"""Audio splitting utilities for speech-to-text processing."""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pydub import AudioSegment

AUDIO_DEPENDENCY_ERROR = ImportError(
    "Optional audio dependencies are required. Please install them via 'pip install stt-utils[audio]'"
)


def split_audio_on_silence(
    audio: "AudioSegment",
    segment_length: float = 600.0,  # in seconds
    segment_delta: float = 30.0,  # in seconds
    silence_thresh_delta: int = -16,  # in dB
    min_silence_len_ms: float = 0.5,  # in seconds
) -> list["AudioSegment"]:
    """Split a pydub AudioSegment into smaller segments with length = (segment_length ± segment_delta) by the longest silences."""
    split_points = find_split_points(
        audio,
        int(segment_length * 1000),
        int(segment_delta * 1000),
        silence_thresh_delta,
        int(min_silence_len_ms * 1000),
    )
    return split_audio_at_points(audio, split_points)


def find_split_points(
    audio: "AudioSegment",
    segment_length_ms: int,
    segment_delta_ms: int,
    silence_thresh_delta: int,
    min_silence_len_ms: int,
) -> list[int]:
    """Find split points in audio based on silence detection."""
    split_points = []
    current_pos = 0
    audio_length = len(audio)
    silence_thresh = int(audio.dBFS + silence_thresh_delta)

    while True:
        split_point = find_next_split_point(
            audio,
            current_pos,
            segment_length_ms,
            segment_delta_ms,
            silence_thresh,
            min_silence_len_ms,
            audio_length,
        )
        if split_point is None:
            break
        split_points.append(split_point)
        current_pos = split_point

    return split_points


def find_next_split_point(
    audio: "AudioSegment",
    current_pos: int,
    segments_length_ms: int,
    segment_delta_ms: int,
    silence_thresh: int,
    min_silence_len_ms: int,
    audio_length: int,
) -> Optional[int]:
    """Find the next optimal split point in audio based on silence."""
    search_delta = int(segment_delta_ms / 2)

    target_split = current_pos + segments_length_ms
    if target_split + search_delta >= audio_length:
        return None

    start_search = max(0, target_split - search_delta)
    end_search = min(audio_length, target_split + search_delta)
    search_segment = audio[start_search:end_search]

    try:
        from pydub.silence import detect_silence
    except ImportError:
        raise AUDIO_DEPENDENCY_ERROR

    silences = detect_silence(
        search_segment,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh,
    )

    if silences:
        longest_duration = 0
        longest_mid = None
        for start_ms, end_ms in silences:
            duration = end_ms - start_ms
            if duration > longest_duration:
                longest_duration = duration
                longest_mid = start_search + (start_ms + end_ms) // 2
        split_point = longest_mid if longest_mid is not None else target_split
    else:
        split_point = target_split

    return split_point


def split_audio_at_points(
    audio: "AudioSegment",
    split_points: list[int],
) -> list["AudioSegment"]:
    """Split audio into segments at specified time points."""
    segments = []
    prev_pos = 0
    for point in split_points:
        segments.append(audio[prev_pos:point])
        prev_pos = point
    if prev_pos < len(audio):
        segments.append(audio[prev_pos:])
    return segments
