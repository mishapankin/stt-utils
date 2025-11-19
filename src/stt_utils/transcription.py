"""Utilities for working with transcriptions."""

import difflib
import os
import re
from dataclasses import dataclass
import textwrap
from typing import Optional, Sequence
import unicodedata
from pydantic import BaseModel


class UnprocessedTimestamp(BaseModel):
    """Represents a timestamped word from raw transcription output."""

    start: float
    end: float
    word: str


class UnprocessedTranscription(BaseModel):
    """Raw transcription data with timestamps for individual words returned by openai whisper"""

    text: str
    duration: float
    words: list[UnprocessedTimestamp]


@dataclass
class Timestamp:
    """Timestamp information for a token in processed transcription."""

    index: int

    start_time: float
    end_time: float


class Transcription:
    """Processed transcription with aligned tokens and timestamps."""

    duration: float
    tokens: list[str]
    timestamps: list[Timestamp]

    def __init__(
        self,
        duration: float = 0.0,
        tokens: Optional[list[str]] = None,
        timestamps: Optional[list[Timestamp]] = None,
    ):
        self.duration = duration
        self.tokens = tokens.copy() if tokens is not None else []
        self.timestamps = timestamps.copy() if timestamps is not None else []

    @classmethod
    def from_unprocessed_transcription(
        cls,
        unprocessed: UnprocessedTranscription,
    ) -> "Transcription":
        """Build a Transcription from UnprocessedTranscription by aligning tokens."""
        duration = unprocessed.duration
        tokens = [tok for tok in re.split(r"(\w+)", unprocessed.text) if tok != ""]

        tokens_mapping = dict()
        normalized_tokens: list[str] = []

        for i, tok in enumerate(tokens):
            normalized = normalize_word(tok)
            if normalized != "" and normalized.isalnum():
                tokens_mapping[len(normalized_tokens)] = i
                normalized_tokens.append(normalized)

        timestamped_words = [normalize_word(w.word) for w in unprocessed.words]

        timestamps = []
        matcher = difflib.SequenceMatcher(None, normalized_tokens, timestamped_words)
        for match in matcher.get_matching_blocks():
            for i in range(match.size):
                token_index = tokens_mapping[match.a + i]
                timestamp_index = match.b + i

                word_info = unprocessed.words[timestamp_index]

                timestamp = Timestamp(
                    index=token_index,
                    start_time=word_info.start,
                    end_time=word_info.end,
                )
                timestamps.append(timestamp)

        return cls(
            duration=duration,
            tokens=tokens,
            timestamps=timestamps,
        )

    @classmethod
    def from_sequence(
        cls,
        seq: Sequence["Transcription"],
        sep: Optional[str] = " ",
    ) -> "Transcription":
        """Build a Transcription from merging multiple Transcriptions into one with adjusted indices."""
        duration = sum(t.duration for t in seq)
        tokens = []
        timestamps = []

        offset = 0
        for i, transcription in enumerate(seq):
            tokens.extend(transcription.tokens)
            for ts in transcription.timestamps:
                new_ts = Timestamp(
                    index=ts.index + offset,
                    start_time=ts.start_time,
                    end_time=ts.end_time,
                )
                timestamps.append(new_ts)
            offset += len(transcription.tokens)

            if sep is not None and i < len(seq) - 1:
                tokens.append(sep)
                offset += 1

        return cls(
            duration=duration,
            tokens=tokens,
            timestamps=timestamps,
        )

    def get_text(self) -> str:
        """Get the full text by joining all tokens."""
        return "".join(self.tokens)

    def _get_preview_markers(self) -> str:
        """Generate marker string showing timestamped positions."""
        markers = [" " * len(c) for c in self.tokens]
        for ts in self.timestamps:
            markers[ts.index] = "^" * len(self.tokens[ts.index])

        return "".join(markers)

    def get_word_by_timestamp(self, timestamp: Timestamp) -> str:
        """Get the token corresponding to a timestamp."""
        return self.tokens[timestamp.index]

    def dumps_preview(self) -> str:
        """Generate a preview string with text and timestamp markers under without wrapping."""
        return self.get_text() + "\n" + self._get_preview_markers()

    def dumps_preview_wrapped(self, width: int) -> str:
        """Generate wrapped preview with text and markers at specified width."""
        if width <= 0:
            raise ValueError("Wrapping width must be positive")

        text = self.get_text()

        wrapper = textwrap.TextWrapper(
            width=width, break_long_words=True, replace_whitespace=False
        )
        lines = wrapper.wrap(text)

        pos = 0
        output_lines = []
        markers = self._get_preview_markers()

        for line in lines:
            start = text.find(line, pos)
            if start == -1:
                start = pos
                line = text[start : start + min(width, len(text) - start)]

            output_lines.append(text[start : start + len(line)])
            output_lines.append(markers[start : start + len(line)])
            output_lines.append("")

            pos = start + len(line)

        return "\n".join(output_lines)

    def dump_preview(self, width: Optional[int] = None) -> None:
        """Print preview to console, wrapping to terminal width if possible."""
        if width is None:
            try:
                width = os.get_terminal_size().columns
            except OSError:
                print(self.dumps_preview())
                return
        print(self.dumps_preview_wrapped(width))


def normalize_word(word: str) -> str:
    """Normalize a word by lowercasing and removing diacritics."""
    word = word.lower().strip()
    word = unicodedata.normalize("NFD", word)
    word = "".join(c for c in word if unicodedata.category(c) != "Mn")
    return word
