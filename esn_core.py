"""
Echo state network instrument: your keyboard (Q..P) drives a reservoir,
and the reservoir's node activations become sound in Sardine.

Pure numpy + threading, no Sardine dependency, so it can be imported and
tested anywhere. esn_live.py wires it to Sardine.
"""
import threading
import time

import numpy as np

KEYS = "qwertyuiop"  # 10 input channels


class ESN:
    """Leaky-integrator echo state network with live 'hotwire' loops."""

    def __init__(self, n=200, density=0.1, rho=0.95, leak=0.3,
                 in_scale=1.0, noise=1e-3, seed=0):
        self.rng = np.random.default_rng(seed)
        self.n, self.leak, self.noise = n, leak, noise

        W = self.rng.standard_normal((n, n)) * (self.rng.random((n, n)) < density)
        W /= np.max(np.abs(np.linalg.eigvals(W)))  # unit spectral radius
        self._W_base = W
        self._rho = rho
        self.W_in = self.rng.uniform(-in_scale, in_scale, (n, len(KEYS)))

        self.hot = np.zeros((n, n))  # hand-wired extra connections
        self.loops = []              # list of (kind, [nodes])
        self._rebuild()

        self.x = np.zeros(n)                 # reservoir state
        self.u = np.zeros(len(KEYS))         # smoothed input envelope
        self.held = np.zeros(len(KEYS))      # raw key state (0/1)

    # ---- knobs you can turn live ---------------------------------------
    @property
    def rho(self):
        return self._rho

    @rho.setter
    def rho(self, value):
        """Spectral radius. <1: echoes fade. ~1: long tails. >1: chaos."""
        self._rho = value
        self._rebuild()

    def hotwire(self, n_loops=3, length=5, gain=3.0, kind="osc"):
        """Wire random nodes into small rings.

        kind="osc":   ring with one inhibitory edge -> self-sustaining oscillator.
                      At 100 Hz stepping: length 3 ~7 Hz, 5 ~3.7 Hz, 7 ~2.6 Hz, 9 ~2 Hz.
        kind="latch": all-excitatory ring -> remembers a kick and stays on
        Returns the node indices of the new loops.
        """
        new = []
        for _ in range(n_loops):
            nodes = self.rng.choice(self.n, length, replace=False)
            for a, b in zip(nodes, np.roll(nodes, -1)):
                self.hot[b, a] += gain
            if kind == "osc":
                self.hot[nodes[0], nodes[-1]] *= -1
            self.loops.append((kind, nodes.tolist()))
            new.append(nodes.tolist())
        self._rebuild()
        return new

    def unwire(self):
        """Remove every hotwire loop."""
        self.hot[:] = 0
        self.loops = []
        self._rebuild()

    def kick(self, amount=1.0):
        """Shove the whole reservoir (useful to restart dead loops)."""
        self.x += amount * self.rng.standard_normal(self.n)

    def loop_nodes(self):
        return [i for _, nodes in self.loops for i in nodes]

    # ---- dynamics -------------------------------------------------------
    def _rebuild(self):
        self.W = self._rho * self._W_base + self.hot

    def step(self, attack=0.5, release=0.05):
        rate = np.where(self.held > self.u, attack, release)
        self.u += rate * (self.held - self.u)
        pre = self.W @ self.x + self.W_in @ self.u
        pre += self.noise * self.rng.standard_normal(self.n)
        self.x = (1 - self.leak) * self.x + self.leak * np.tanh(pre)
        return self.x

    def energy(self):
        return float(np.mean(np.abs(self.x)))


class Runner(threading.Thread):
    """Steps the ESN at a fixed rate in the background."""

    def __init__(self, esn, hz=100):
        super().__init__(daemon=True)
        self.esn, self.dt, self.running = esn, 1.0 / hz, True

    def run(self):
        while self.running:
            t0 = time.perf_counter()
            self.esn.step()
            time.sleep(max(0.0, self.dt - (time.perf_counter() - t0)))

    def stop(self):
        self.running = False


class Keyboard:
    """Global Q..P listener. F8 arms/disarms so typing code doesn't play notes."""

    def __init__(self, esn, armed=False):
        from pynput import keyboard  # imported here so tests don't need it
        self.esn, self.armed = esn, armed
        self._kb = keyboard
        self.listener = keyboard.Listener(on_press=self._press,
                                          on_release=self._release)
        self.listener.start()

    def _idx(self, key):
        c = getattr(key, "char", None)
        return KEYS.index(c.lower()) if c and c.lower() in KEYS else None

    def _press(self, key):
        if key == self._kb.Key.f8:
            self.armed = not self.armed
            self.esn.held[:] = 0
            print(f"\n[esn] keyboard {'ARMED' if self.armed else 'off'}")
            return
        i = self._idx(key)
        if self.armed and i is not None:
            self.esn.held[i] = 1.0

    def _release(self, key):
        i = self._idx(key)
        if i is not None:
            self.esn.held[i] = 0.0

    def stop(self):
        self.listener.stop()


# ---- musical helpers ----------------------------------------------------
MINOR_PENTA = [0, 3, 5, 7, 10]


def to_note(v, root=48, span=12, scale=MINOR_PENTA):
    """Map an activation in [-1, 1] to a MIDI note on a scale."""
    deg = int(np.clip((v + 1) / 2, 0, 0.999) * span)
    return root + 12 * (deg // len(scale)) + scale[deg % len(scale)]
