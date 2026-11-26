"""
Render the ESN instrument to a WAV with plain numpy synthesis (no Sardine,
no SuperCollider). Plays a scripted key sequence, hotwires loops halfway,
and writes esn_demo.wav.

    python esn_offline.py
"""
import wave

import numpy as np

from esn_core import ESN, KEYS, to_note

SR, BPM, SECONDS, STEP_HZ = 44100, 120, 24, 100
STEP16 = 60 / BPM / 4                       # sixteenth-note length (s)


def midi_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tone(freq, dur, amp, kind="sine"):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 6)
    if kind == "saw":
        w = 2 * ((t * freq) % 1) - 1
        w = np.convolve(w, np.ones(8) / 8, "same")
    else:
        w = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return amp * env * w


def drum(kind, amp, rng):
    t = np.arange(int(0.25 * SR)) / SR
    if kind == "bd":
        return amp * np.sin(2 * np.pi * (50 + 100 * np.exp(-t * 30)) * t) * np.exp(-t * 12)
    if kind == "sn":
        return amp * 0.6 * rng.standard_normal(t.size) * np.exp(-t * 20)
    n = rng.standard_normal(t.size)
    return amp * 0.3 * np.diff(n, prepend=0) * np.exp(-t * 60)


def main():
    rng = np.random.default_rng(0)
    esn = ESN(seed=7)
    drum_nodes = list(esn.rng.choice(esn.n, 3, replace=False))
    lead_nodes = list(esn.rng.choice(esn.n, 2, replace=False))
    bass_node = int(esn.rng.integers(esn.n))

    # scripted performance: (start_s, end_s, key)
    script = [(0.5, 1.0, "q"), (1.5, 2.0, "t"), (2.5, 3.5, "p"),
              (4.0, 4.3, "w"), (4.5, 4.8, "w"), (6.0, 7.0, "y")]
    hotwire_at = 10.0

    out = np.zeros(int((SECONDS + 1) * SR))
    steps_per_16 = int(round(STEP16 * STEP_HZ))
    wired, step16 = False, 0
    for k in range(int(SECONDS * STEP_HZ)):
        t = k / STEP_HZ
        esn.held[:] = 0
        for a, b, key in script:
            if a <= t < b:
                esn.held[KEYS.index(key)] = 1
        if not wired and t >= hotwire_at:
            esn.hotwire(2, length=5)
            nodes = esn.loop_nodes()
            drum_nodes, lead_nodes = nodes[:3], nodes[3:5]
            esn.kick(0.5)
            wired = True
        esn.step()

        if k % steps_per_16:
            continue
        pos = int(t * SR)
        x = esn.x
        for node, kind in zip(drum_nodes, ["bd", "sn", "hh"]):
            if x[node] > 0.25:
                s = drum(kind, min(1, 0.3 + x[node]), rng)
                out[pos:pos + s.size] += s
        if step16 % 2 == 0 and esn.energy() > 0.02:
            s = tone(midi_hz(to_note(x[lead_nodes[0]], root=60)), 0.4, 0.25)
            out[pos:pos + s.size] += s
        if step16 % 4 == 0 and abs(x[bass_node]) > 0.1:
            s = tone(midi_hz(to_note(x[bass_node], root=36, span=5)), 0.5, 0.3, "saw")
            out[pos:pos + s.size] += s
        step16 += 1

    out = out[: SECONDS * SR]
    out /= max(1e-9, np.max(np.abs(out))) / 0.9
    with wave.open("esn_demo.wav", "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((out * 32767).astype(np.int16).tobytes())
    print("wrote esn_demo.wav")
    return out


if __name__ == "__main__":
    main()
