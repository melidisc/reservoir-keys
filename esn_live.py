# ---------------------------------------------------------------------------
# ESN instrument for Sardine.
# Inside the Sardine REPL (started from this folder):
#     exec(open("esn_live.py").read())
# Then press F8 to arm the keyboard and play Q..P.
# ---------------------------------------------------------------------------
import os, sys
sys.path.insert(0, os.getcwd())

import numpy as np
from esn_core import ESN, Runner, Keyboard, to_note

esn = ESN(n=200, rho=0.95, leak=0.3, seed=7)
runner = Runner(esn, hz=100)
runner.start()
kb = Keyboard(esn)          # F8 toggles play mode
print("[esn] running. Press F8 to arm the keyboard, then play Q..P")

# Which reservoir nodes drive which voice. Reassign live, e.g.
#   DRUM_NODES = esn.loop_nodes()[:3]
DRUM_NODES = list(esn.rng.choice(esn.n, 3, replace=False))
LEAD_NODES = list(esn.rng.choice(esn.n, 2, replace=False))
BASS_NODE = int(esn.rng.integers(esn.n))
THRESH = 0.25


def fmt(v):
    return f"{float(v):.3f}"


@swim
def drums(p=0.25, i=0):
    # each drum fires when its node is above threshold
    for node, sample in zip(DRUM_NODES, ["bd", "sn", "hh"]):
        v = esn.x[node]
        if v > THRESH:
            D(sample, amp=fmt(min(1.0, 0.3 + v)), i=i)
    again(drums, p=0.25, i=i + 1)


@swim
def lead(p=0.5, i=0):
    a, b = esn.x[LEAD_NODES[0]], esn.x[LEAD_NODES[1]]
    if esn.energy() > 0.02:
        D("superpiano",
          note=str(to_note(a, root=60)),
          cutoff=fmt(400 + 4000 * abs(b)),
          room=fmt(0.2 + 0.6 * esn.energy()),
          i=i)
    again(lead, p=0.5, i=i + 1)


@swim
def bass(p=1, i=0):
    v = esn.x[BASS_NODE]
    if abs(v) > 0.1:
        D("supersaw", note=str(to_note(v, root=36, span=5)),
          cutoff="600", sustain="0.4", i=i)
    again(bass, p=1, i=i + 1)


def hotwire(n=2, length=5, kind="osc"):
    """Wire new loops and point the drums/lead at the looping nodes."""
    global DRUM_NODES, LEAD_NODES
    loops = esn.hotwire(n, length=length, kind=kind)
    nodes = esn.loop_nodes()
    DRUM_NODES = nodes[:3]
    LEAD_NODES = nodes[3:5] if len(nodes) >= 5 else nodes[:2]
    esn.kick(0.5)
    print("[esn] wired", loops)


def unwire():
    esn.unwire()
    print("[esn] all loops removed; echoes will fade")


def stop_esn():
    silence()
    kb.stop()
    runner.stop()
