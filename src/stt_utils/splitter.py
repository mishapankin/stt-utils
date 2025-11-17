try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
except ImportError:
    raise ImportError(
        "pydub is required for audio splitting. Install optional audio support: pip install stt-utils[audio]."
    )

from typing import Optional


# Split a pydub AudioSegment into smaller segments with length of segments_approx_length_ms ± delta_ms on the longest silence.
def split_audio_on_silence(
    audio: AudioSegment,
    segments_approx_length_ms: int,
    segment_delta_ms: int,
    silence_thresh_delta=-16,
    min_silence_len_ms=500,
) -> list[AudioSegment]:
    split_points = find_split_points(
        audio,
        segments_approx_length_ms,
        segment_delta_ms,
        silence_thresh_delta,
        min_silence_len_ms,
    )
    return split_audio_at_points(audio, split_points)


def find_split_points(
    audio: AudioSegment,
    segments_approx_length_ms: int,
    segment_delta_ms: int,
    silence_thresh_delta=-16,
    min_silence_len_ms=500,
) -> list[int]:
    split_points = []
    current_pos = 0
    audio_length = len(audio)
    silence_thresh = int(audio.dBFS + silence_thresh_delta)

    while True:
        split_point = find_next_split_point(
            audio,
            current_pos,
            segments_approx_length_ms,
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
    audio: AudioSegment,
    current_pos: int,
    segments_approx_length_ms: int,
    segment_delta_ms: int,
    silence_thresh: int,
    min_silence_len_ms: int,
    audio_length: int,
) -> Optional[int]:
    target_split = current_pos + segments_approx_length_ms
    if target_split >= audio_length:
        return None

    start_search = max(0, target_split - segment_delta_ms)
    end_search = min(audio_length, target_split + segment_delta_ms)
    search_segment = audio[start_search:end_search]

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
    audio: AudioSegment, split_points: list[int]
) -> list[AudioSegment]:
    segments = []
    prev_pos = 0
    for point in split_points:
        segments.append(audio[prev_pos:point])
        prev_pos = point
    if prev_pos < len(audio):
        segments.append(audio[prev_pos:])
    return segments
