# Sardine starter patterns.
# Inside the Sardine REPL:  exec(open("starter.py").read())
# Edit a function and re-run it: the loop updates on the next beat.

# Shorthand player: kick, hat, snare, hat ('.' = rest)
Pa >> d('bd . hh . sn . hh')


# Temporal recursion: a function that reschedules itself
@swim
def beat(p=0.5, i=0):
    D('bd', i=i)
    D('hh', speed='2', i=i)
    again(beat, p=0.5, i=i + 1)

# silence()   # stop everything
