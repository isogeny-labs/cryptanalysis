# M31 packed public fiber replay

Build the four reference libraries following the adjacent m31-native-smooth-filter
instructions. From this directory, compile the distinct validator and pass the
absolute paths to the lift, layer, fiber and smooth-filter libraries in that order.

```sh
cc -O3 -shared -fPIC distinct.c -o /tmp/m31-distinct.so
python3 distinct_replay.py "$lift" "$layer" "$fiber" "$filter" /tmp/m31-distinct.so
```

Use Python with SymPy and assertions enabled. Each timed call regenerates the
depth-15 public basis and is checked against the ordered reference. The control
uses a set to check distinctness. The candidate rejects equal siblings at each
level of the fold. Fold.lean proves the sibling and indexing properties under
the field hypotheses. Words.lean checks the word arithmetic. The benchmark
begins after process startup and library loading.
