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
    index: int

    start_time: float
    end_time: float


class Transcription:
    tokens: list[str]
    timestamps: list[Timestamp]

    def __init__(self, unprocessed: UnprocessedTranscription):
        text = unprocessed.text
        self.timestamps = []

        self.tokens = [tok for tok in re.split(r"(\w+)", text) if tok != ""]

        normalized_tokens = [normalize_word(tok) for tok in self.tokens]
        timestamped_words = [normalize_word(w.word) for w in unprocessed.words]

        matcher = difflib.SequenceMatcher(None, normalized_tokens, timestamped_words)
        for match in matcher.get_matching_blocks():
            for i in range(match.size):
                idx1 = match.a + i
                idx2 = match.b + i

                word_info = unprocessed.words[idx2]

                timestamp = Timestamp(
                    index=idx1,
                    start_time=word_info.start,
                    end_time=word_info.end,
                )
                self.timestamps.append(timestamp)

    def get_text(self) -> str:
        return "".join(self.tokens)

    def _get_preview_markers(self) -> str:
        text = self.get_text()
        t = [" " * len(c) for c in self.tokens]
        for ts in self.timestamps:
            t[ts.index] = "^" * len(self.tokens[ts.index])

        return "".join(t)

    def get_word_by_timestamp(self, timestamp: Timestamp) -> str:
        return self.tokens[timestamp.index]

    def dumps_preview(self) -> str:
        return self.get_text() + "\n" + self._get_preview_markers()

    def dumps_preview_wrapped(self, width: int) -> str:
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
