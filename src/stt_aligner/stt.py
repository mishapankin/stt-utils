import difflib
import os
import re
from dataclasses import dataclass
import textwrap
from typing import Optional
import unicodedata
from pydantic import BaseModel


class UnprocessedTimestamp(BaseModel):
    start: float
    end: float
    word: str


class UnprocessedTranscription(BaseModel):
    text: str
    words: list[UnprocessedTimestamp]


@dataclass
class Timestamp:
    start_index: int
    end_index: int

    start_time: float = None
    end_time: float = None


class Transcription:
    text: str
    timestamps: list[Timestamp]

    def __init__(self, unprocessed: UnprocessedTranscription):
        self.text = unprocessed.text
        self.timestamps = []

        original_indicies = []
        original_words = []

        for match in re.finditer(r"\w+", self.text):
            original_indicies.append(match.span())
            original_words.append(normalize_word(match.group(0)))

        timestamped_words = [normalize_word(w.word) for w in unprocessed.words]

        matcher = difflib.SequenceMatcher(None, original_words, timestamped_words)
        for match in matcher.get_matching_blocks():
            for i in range(match.size):
                idx1 = match.a + i
                idx2 = match.b + i

                start_idx, end_idx = original_indicies[idx1]
                word_info = unprocessed.words[idx2]

                timestamp = Timestamp(
                    start_index=start_idx,
                    end_index=end_idx,
                    start_time=word_info.start,
                    end_time=word_info.end,
                )
                self.timestamps.append(timestamp)

    def _get_preview_markers(self) -> str:
        t = [" "] * len(self.text)

        for ts in self.timestamps:
            for i in range(ts.start_index, ts.end_index):
                if 0 <= i < len(t):
                    t[i] = "^"

        return "".join(t)

    def get_word_by_timestamp(self, timestamp: Timestamp) -> str:
        return self.text[timestamp.start_index : timestamp.end_index]

    def dumps_preview(self) -> str:
        return self.text + "\n" + self._get_preview_markers()

    def dumps_preview_wrapped(self, width: int) -> str:
        if width <= 0:
            raise ValueError("Wrapping width must be positive")

        wrapper = textwrap.TextWrapper(
            width=width, break_long_words=True, replace_whitespace=False
        )
        lines = wrapper.wrap(self.text)

        pos = 0
        output_lines = []
        markers = self._get_preview_markers()

        for line in lines:
            start = self.text.find(line, pos)
            if start == -1:
                start = pos
                line = self.text[start : start + min(width, len(self.text) - start)]

            output_lines.append(self.text[start : start + len(line)])
            output_lines.append(markers[start : start + len(line)])
            output_lines.append("")

            pos = start + len(line)

        return "\n".join(output_lines)

    def dump_preview(self, width: Optional[int] = None) -> None:
        if width is None:
            try:
                width = os.get_terminal_size().columns
            except OSError:
                print(self.dumps_preview())
                return
        print(self.dumps_preview_wrapped(width))


def normalize_word(word: str) -> str:
    word = word.lower().strip()
    word = unicodedata.normalize("NFD", word)
    word = "".join(c for c in word if unicodedata.category(c) != "Mn")
    return word
