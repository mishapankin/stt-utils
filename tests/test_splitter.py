import unittest
from pydub.generators import Sine
from pydub import AudioSegment
from stt_utils import split_audio_on_silence
from stt_utils.splitter import find_split_points


class TestSplitter(unittest.TestCase):
    def test_split_audio_on_silence_synthetic(self):
        dur_1 = 62
        dur_2 = 63
        dur_silence = 2

        wave1 = Sine(440).to_audio_segment(duration=dur_1 * 1000, volume=-10)
        wave2 = Sine(440 * 2).to_audio_segment(duration=dur_2 * 1000, volume=-8)

        silence = AudioSegment.silent(dur_silence * 1000)

        combined = wave1 + silence + wave2

        splitted = split_audio_on_silence(
            audio=combined,
            segment_length=60,
            segment_delta=10,
        )

        res_dur_1 = len(splitted[0]) * 0.001
        res_dur_2 = len(splitted[1]) * 0.001

        self.assertEqual(len(splitted), 2)
        self.assertAlmostEqual(dur_1 + dur_silence / 2, res_dur_1, 1)
        self.assertAlmostEqual(dur_2 + dur_silence / 2, res_dur_2, 1)


if __name__ == "__main__":
    unittest.main()
