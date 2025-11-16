import unittest
from stt_aligner import normalize_word, Transcription, UnprocessedTranscription
import re


class TestAligner(unittest.TestCase):
    def test_utf_normalization(self):
        self.assertEqual(normalize_word("café"), "cafe")
        self.assertEqual(normalize_word("naïve"), "naive")
        self.assertEqual(normalize_word("résumé"), "resume")
        self.assertEqual(normalize_word("coöperate"), "cooperate")
        self.assertEqual(normalize_word("São Paulo"), "sao paulo")

    def test_aligner(self):
        with open("tests/assets/homer.json", "r") as file:
            data = file.read()

        unprocessed = UnprocessedTranscription.model_validate_json(data)
        transcription = Transcription.from_unprocessed_transcription(unprocessed)

        for ts in transcription.timestamps:
            self.assertTrue(0 <= ts.index < len(transcription.tokens))
            self.assertTrue(re.match(r"\w+", transcription.get_word_by_timestamp(ts)))
            self.assertIsNotNone(ts.start_time)
            self.assertIsNotNone(ts.end_time)


if __name__ == "__main__":
    unittest.main()
