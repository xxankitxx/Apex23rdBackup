"""2 Nov 2026: speaker cues exist only for trades of the champion and the day's learning; they are loud and mono."""
import numpy as np

from apex import audio


def test_four_cues_only_trade_events():
    assert set(audio.CUES) == {"entry", "win", "loss", "learn"}      # no "armed", no spike, no commentary


def test_cues_are_loud_short_and_click_free():
    for kind, fn in audio.CUES.items():
        a = np.frombuffer(fn(), "<i2").astype(float)
        assert 0.4 <= len(a) / audio.SR <= 1.8, kind                   # a cue, not a jingle
        assert abs(a).max() >= 0.9 * 32767, kind                       # peak-normalised: loud
        assert abs(a[-1]) < 300 and abs(a[0]) < 300, kind              # starts and ends at silence: no click


def test_fit_matches_the_mixer_that_opened():
    mono = audio.cue_entry()
    n = len(mono) // 2
    assert len(audio._fit(mono, (audio.SR, -16, 1))) == 2 * n
    assert len(audio._fit(mono, (audio.SR, -16, 2))) == 4 * n          # stereo: every sample doubled, same length in time
    assert abs(len(audio._fit(mono, (22050, -16, 1))) // 2 - n // 2) <= 1


def test_play_is_silent_before_init_and_for_unknown_kinds():
    audio.play("armed")
    audio.play("entry")


def test_note_table():
    assert abs(audio.hz("A4") - 440.0) < 1e-9
    assert abs(audio.hz("C5") - 523.25) < 0.01
    assert abs(audio.hz("F#4") - 369.99) < 0.01
