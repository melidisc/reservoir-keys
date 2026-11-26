# ESN instrument for Sardine

Your keyboard (Q..P = 10 input channels) drives a 200-node echo state network.
Reservoir nodes trigger drums, a lead and a bass in Sardine. Hotwire random
nodes into rings and they keep oscillating on their own.

## Files
- `starter.py`: the basic Sardine patterns
- `esn_core.py`: the ESN, background runner and keyboard listener (numpy only)
- `esn_live.py`: wires the ESN to Sardine voices
- `esn_offline.py`: renders `esn_demo.wav` with numpy synthesis, no Sardine needed
- `web/index.html`: the same network in the browser (Web Audio), with clickable
  keys, sliders, hotwire buttons and a water-ripple view of the neurons.
  Open it directly in a browser, no server needed.

## Setup (Python 3.11 venv recommended)
```bash
python -m pip install sardine-system numpy pynput
```
Install SuperCollider, then run `Quarks.install("SuperDirt")` in it once.

macOS: give your terminal Input Monitoring permission (System Settings >
Privacy & Security) so pynput can read keys. Linux on Wayland: pynput may not
see keys; use an X11 session.

## Play
```bash
cd this-folder
sardine
```
Then in the Sardine REPL:
```python
exec(open("esn_live.py").read())
```
- **F8** arms/disarms the keyboard (so typing code doesn't play notes)
- Hold **Q..P** to push signal in; echoes ring and fade

## Live knobs
```python
hotwire()                   # 2 oscillator rings, voices follow the loop nodes
hotwire(1, length=9)        # slower ring (~2 Hz)
hotwire(1, kind="latch")    # a ring that remembers a kick and stays on
unwire()                    # back to fading echoes
esn.rho = 1.05              # edge of chaos; 0.8 = short, dry echoes
esn.leak = 0.1              # slower, smoother reservoir
esn.kick()                  # shove the whole network
THRESH = 0.1                # busier drums
silence()                   # stop sound;  stop_esn() stops everything
```
Edit any `@swim` function in `esn_live.py` and re-run it to change the music.

Loop-length rates at 100 Hz stepping: 3 nodes ~7 Hz, 5 ~3.7 Hz, 7 ~2.6 Hz, 9 ~2 Hz.
