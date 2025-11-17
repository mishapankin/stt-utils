try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
except ImportError:
    raise ImportError(
        "pydub is required for audio splitting. Install optional audio support: pip install stt-utils[audio]."
    )


# Split a pydub AudioSegment into smaller segments with length of segments_approx_length_ms ± delta_ms on the longest silence.
def split_audio_on_silence(
    audio: AudioSegment,
    segments_approx_length_ms: int,
    segment_delta_ms: int,
    silence_thresh_delta=-16,
    min_silence_len_ms=500,
) -> list[AudioSegment]:
    segments = []
    current_pos = 0
    audio_length = len(audio)
    silence_thresh = int(audio.dBFS + silence_thresh_delta)

    while current_pos < audio_length:
        target_split = current_pos + segments_approx_length_ms
        if target_split >= audio_length:
            segments.append(audio[current_pos:])
            break

        # Look for silence in [target_split - delta_ms, target_split + delta_ms]
        start_search = max(0, target_split - segment_delta_ms)
        end_search = min(audio_length, target_split + segment_delta_ms)
        search_segment = audio[start_search:end_search]

        silences = detect_silence(
            search_segment,
            min_silence_len=min_silence_len_ms,
            silence_thresh=silence_thresh,
        )

        if silences:
            # Find the longest silence
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

        segments.append(audio[current_pos:split_point])
        current_pos = split_point

    return segments
