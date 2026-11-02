"""
Audio alerts, played from the ENGINE on the PC speaker (a browser tab can be muted or hidden; this cannot).

2 Nov 2026 (owner: "no unnecessary sound if there was no event like an entry"): a sound plays ONLY when the
champion book trades, and once when the day is learned. The Triangle "armed" chime, the straddle-spike chime
and the browser's commentary beeps are gone — none of them is a trade.

Cues (original chiptune-style synthesis, loud, nothing borrowed from any game or other project):
  entry — power-up: a fast rising major arpeggio that lands on a held top note   (the champion BOUGHT)
  win   — fanfare: three short hits, a long fifth, then a sustained major chord   (SOLD in profit)
  loss  — game over: four descending notes, the last one sagging and wobbling    (SOLD at a loss)
  learn — stage clear: a bright two-bell chime with a sparkle on top             (the day was learned)

Each cue is rendered once at init() with numpy at 44.1 kHz, peak-normalised and soft-clipped (loud, no
distortion). The browser (static/app.js, sfx()) plays the same four recipes through Web Audio.
Set config.AUDIO = False to silence the engine entirely.
"""
import math
import threading

import numpy as np

from . import config

SR = 44100

# Note names -> Hz (equal temperament, A4 = 440)
_NOTE = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


def hz(name):
    """C5 -> 523.25, F#4 -> 369.99"""
    octave = int(name[-1])
    return 440.0 * 2 ** ((_NOTE[name[:-1]] + 12 * (octave - 4)) / 12.0)


def _wave(kind, phase):
    """phase in cycles; square and saw are softened with a little sine (less harsh at volume)."""
    x = phase - np.floor(phase)
    if kind == "square":
        return np.where(x < 0.5, 1.0, -1.0) * 0.8 + 0.2 * np.sin(2 * np.pi * x)
    if kind == "triangle":
        return 4.0 * np.abs(x - 0.5) - 1.0
    if kind == "saw":
        return (2.0 * x - 1.0) * 0.85 + 0.15 * np.sin(2 * np.pi * x)
    return np.sin(2 * np.pi * x)


def voice(freq, ms, kind="square", gain=0.5, attack_ms=4.0, decay=1.0, slide=0.0, vib_hz=0.0, vib=0.0, sr=SR):
    """One note: freq (Hz, gliding to freq*(1+slide) over its length), ms long.
    decay: 0 = flat sustain, 1 = fades to ~0 by the end; vib = fractional pitch wobble at vib_hz."""
    n = max(2, int(sr * ms / 1000.0))
    t = np.arange(n) / sr
    f = freq * (1.0 + slide * t / t[-1])
    if vib and vib_hz:
        f = f * (1.0 + vib * np.sin(2 * np.pi * vib_hz * t))
    phase = np.cumsum(f) / sr
    env = np.minimum(1.0, t / max(1e-4, attack_ms / 1000.0))
    if decay > 0:
        env = env * np.exp(-decay * 5.0 * t / t[-1])
    tail = min(n, int(sr * 0.004))
    env[-tail:] = env[-tail:] * np.linspace(1.0, 0.0, tail)          # click-free end
    return gain * env * _wave(kind, phase)


def _render(parts, total_ms, sr=SR):
    """parts: [(start_ms, samples)]; mixed, peak-normalised and soft-clipped; 16-bit mono bytes."""
    out = np.zeros(int(sr * total_ms / 1000.0) + 1)
    for start_ms, snd in parts:
        i = int(sr * start_ms / 1000.0)
        j = min(len(out), i + len(snd))
        if j > i:
            out[i:j] += snd[:j - i]
    pk = float(np.max(np.abs(out))) or 1.0
    out = np.tanh(1.6 * out / pk) / math.tanh(1.6)                   # loud, rounded, never clips
    return (out * 32767 * 0.98).astype("<i2").tobytes()


def cue_entry():
    """Power-up: C5 E5 G5 C6 E6 G6 at 48 ms each, then C7 held 320 ms."""
    parts, t = [], 0.0
    for nm in ("C5", "E5", "G5", "C6", "E6", "G6"):
        parts.append((t, voice(hz(nm), 60, "square", 0.55, decay=0.4)))
        parts.append((t, voice(hz(nm) / 2, 60, "triangle", 0.25, decay=0.4)))
        t += 48.0
    parts.append((t, voice(hz("C7"), 320, "square", 0.6, decay=1.0, vib_hz=18.0, vib=0.006)))
    parts.append((t, voice(hz("C6"), 320, "triangle", 0.3, decay=1.0)))
    return _render(parts, t + 340)


def cue_win():
    """Fanfare: C5 C5 C5 . G5 (long), then a C-major chord with a shimmer on top."""
    parts = []
    for start in (0.0, 130.0, 260.0):
        parts.append((start, voice(hz("C5"), 110, "square", 0.5, decay=0.6)))
        parts.append((start, voice(hz("C4"), 110, "triangle", 0.3, decay=0.6)))
    parts.append((420.0, voice(hz("G5"), 380, "square", 0.55, decay=0.35)))
    parts.append((420.0, voice(hz("G4"), 380, "triangle", 0.3, decay=0.35)))
    for nm, g in (("C5", 0.32), ("E5", 0.28), ("G5", 0.28), ("C6", 0.34)):
        parts.append((800.0, voice(hz(nm), 700, "square", g, decay=0.9, vib_hz=6.0, vib=0.004)))
    parts.append((800.0, voice(hz("C4"), 700, "triangle", 0.35, decay=0.9)))
    parts.append((860.0, voice(hz("E6"), 500, "sine", 0.22, decay=1.0)))
    return _render(parts, 1520)


def cue_loss():
    """Game over: E5 C5 A4, then F#4 sagging a third and wobbling, saw over a sub bass."""
    parts, t = [], 0.0
    for nm in ("E5", "C5", "A4"):
        parts.append((t, voice(hz(nm), 200, "saw", 0.5, decay=0.5)))
        parts.append((t, voice(hz(nm) / 2, 200, "square", 0.3, decay=0.5)))
        t += 210.0
    parts.append((t, voice(hz("F#4"), 560, "saw", 0.55, decay=0.8, slide=-0.18, vib_hz=7.0, vib=0.02)))
    parts.append((t, voice(hz("F#3"), 560, "square", 0.35, decay=0.8, slide=-0.18)))
    parts.append((t, voice(hz("F#2"), 560, "sine", 0.4, decay=0.8, slide=-0.18)))
    return _render(parts, t + 580)


def cue_learn():
    """Stage clear: A5 then D6 bells, an E6/A6 sparkle on top."""
    parts = []
    for start, nm, g in ((0.0, "A5", 0.5), (160.0, "D6", 0.5), (320.0, "E6", 0.3), (400.0, "A6", 0.3)):
        parts.append((start, voice(hz(nm), 520, "sine", g, decay=1.0)))
        parts.append((start, voice(hz(nm) * 2, 260, "sine", g * 0.35, decay=1.0)))
        parts.append((start, voice(hz(nm) * 3, 160, "sine", g * 0.15, decay=1.0)))
    return _render(parts, 980)


CUES = {"entry": cue_entry, "win": cue_win, "loss": cue_loss, "learn": cue_learn}

_ready = False
_sounds = {}
_lock = threading.Lock()


def _open_mixer(pygame):
    """Mono 44.1 kHz exactly as rendered: without allowedchanges=0 SDL opens stereo and a mono buffer plays at
    double speed and half length (the chipmunk bug)."""
    pygame.mixer.init(frequency=SR, size=-16, channels=1, buffer=1024, allowedchanges=0)


def _fit(mono_bytes, got):
    """Match the rendered mono buffer to whatever the mixer actually opened (rate, bits, channels)."""
    rate, size, ch = got
    a = np.frombuffer(mono_bytes, "<i2").astype(float) / 32767.0
    if rate != SR:
        n = int(len(a) * rate / SR)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    if ch > 1:
        a = np.repeat(a[:, None], ch, axis=1).ravel()
    if abs(size) == 8:
        return (a * 127 + (128 if size > 0 else 0)).astype("u1" if size > 0 else "i1").tobytes()
    return (a * 32767).astype("<i2").tobytes() if size < 0 else ((a + 1.0) * 32767).astype("<u2").tobytes()


def init(log=print):
    """Returns a one-line description of what will play, or None if audio is off."""
    global _ready
    if not getattr(config, "AUDIO", True):
        return None
    try:
        import pygame
        _open_mixer(pygame)
        got = pygame.mixer.get_init()
        if not got:
            return None
        for kind, fn in CUES.items():
            snd = pygame.mixer.Sound(buffer=_fit(fn(), got))
            snd.set_volume(1.0)
            _sounds[kind] = snd
        _ready = True
        return "synth " + ", ".join(f"{k} {_sounds[k].get_length():.1f}s" for k in CUES)
    except Exception as e:
        log(f"audio disabled ({e}); pip install pygame numpy to enable")
        return None


def play(kind):
    """Non-blocking; unknown kinds, and anything before init(), are silent."""
    if not _ready or kind not in _sounds:
        return
    try:
        import pygame
        with _lock:
            if not pygame.mixer.get_init():
                _open_mixer(pygame)
            _sounds[kind].play()
    except Exception:
        pass
