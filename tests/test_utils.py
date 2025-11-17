import unittest
from stt_utils import (
    normalize_word,
    Transcription,
    UnprocessedTranscription,
    Timestamp,
)
import re


class TestAligner(unittest.TestCase):
    def test_utf_normalization(self):
        self.assertEqual(normalize_word("café"), "cafe")
        self.assertEqual(normalize_word("naïve"), "naive")
        self.assertEqual(normalize_word("résumé"), "resume")
        self.assertEqual(normalize_word("coöperate"), "cooperate")
        self.assertEqual(normalize_word("São Paulo"), "sao paulo")

    def test_from_unprocessed_transcription(self):
        with open("tests/assets/homer.json", "r") as file:
            data = file.read()

        unprocessed = UnprocessedTranscription.model_validate_json(data)
        transcription = Transcription.from_unprocessed_transcription(unprocessed)

        for ts in transcription.timestamps:
            self.assertTrue(0 <= ts.index < len(transcription.tokens))
            self.assertTrue(re.match(r"\w+", transcription.get_word_by_timestamp(ts)))
            self.assertIsNotNone(ts.start_time)
            self.assertIsNotNone(ts.end_time)

    def test_from_sequence(self):
        t1 = Transcription(
            duration=1.0,
            tokens=["hello", " ", "world"],
            timestamps=[
                Timestamp(index=0, start_time=0.0, end_time=0.5),
                Timestamp(index=2, start_time=0.5, end_time=1.0),
            ],
        )
        t2 = Transcription(
            duration=2.0,
            tokens=["foo", " ", "bar"],
            timestamps=[
                Timestamp(index=0, start_time=1.0, end_time=1.5),
                Timestamp(index=2, start_time=1.5, end_time=2.0),
            ],
        )

        # Test without a separator
        combined = Transcription.from_sequence([t1, t2], sep=None)
        self.assertEqual(combined.duration, 3.0)
        self.assertEqual(combined.tokens, ["hello", " ", "world", "foo", " ", "bar"])
        self.assertEqual(len(combined.timestamps), 4)
        self.assertEqual(combined.timestamps[0].index, 0)
        self.assertEqual(combined.timestamps[0].start_time, 0.0)
        self.assertEqual(combined.timestamps[1].index, 2)
        self.assertEqual(combined.timestamps[1].start_time, 0.5)
        self.assertEqual(combined.timestamps[2].index, 3)
        self.assertEqual(combined.timestamps[2].start_time, 1.0)
        self.assertEqual(combined.timestamps[3].index, 5)
        self.assertEqual(combined.timestamps[3].start_time, 1.5)

        # Test with a separator
        combined_sep = Transcription.from_sequence([t1, t2], sep="|")
        self.assertEqual(combined_sep.duration, 3.0)
        self.assertEqual(
            combined_sep.tokens, ["hello", " ", "world", "|", "foo", " ", "bar"]
        )
        self.assertEqual(len(combined_sep.timestamps), 4)


if __name__ == "__main__":
    unittest.main()
