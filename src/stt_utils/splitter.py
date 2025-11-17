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


def main():
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Split audio file on silence into multiple segments."
    )
    parser.add_argument("audio_file", help="Path to the audio file to split")
    parser.add_argument(
        "--segment-length",
        type=float,
        default=600.0,
        help="Target segment length in seconds (default: 600)",
    )
    parser.add_argument(
        "--segment-delta",
        type=float,
        default=30.0,
        help="Allowed deviation from segment length in seconds (default: 30)",
    )
    parser.add_argument(
        "--silence-thresh-delta",
        type=int,
        default=-16,
        help="Silence threshold delta in dB (default: -16)",
    )
    parser.add_argument(
        "--min-silence-len",
        type=float,
        default=0.5,
        help="Minimum silence length in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory for split segments (default: current directory)",
    )

    args = parser.parse_args()

    try:
        from pydub import AudioSegment
    except ImportError:
        print(AUDIO_DEPENDENCY_ERROR, file=sys.stderr)
        sys.exit(1)

    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"Error: Audio file '{audio_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio = AudioSegment.from_file(str(audio_path))
    except Exception as e:
        print(f"Error loading audio file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        segments = split_audio_on_silence(
            audio,
            segment_length=args.segment_length,
            segment_delta=args.segment_delta,
            silence_thresh_delta=args.silence_thresh_delta,
            min_silence_len_ms=args.min_silence_len,
        )
    except Exception as e:
        print(f"Error splitting audio: {e}", file=sys.stderr)
        sys.exit(1)

    stem = audio_path.stem
    suffix = audio_path.suffix

    for i, segment in enumerate(segments):
        output_path = output_dir / f"{stem}_part{i + 1:03d}{suffix}"
        try:
            segment.export(str(output_path), format=suffix.lstrip("."))
            print(f"Exported segment {i + 1} to {output_path}")
        except Exception as e:
            print(f"Error exporting segment {i + 1}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Successfully split audio into {len(segments)} segments")


if __name__ == "__main__":
    main()
