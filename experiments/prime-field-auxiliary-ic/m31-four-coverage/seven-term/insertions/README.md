# Single-generator insertion census

The 121 rows in counts.csv identify generators by their index and abscissa
in the frozen 195-generator basis. The complement is the 74-generator core.
Run `python3 replay.py` to compile the pinned census and recompute every
count in reversed generator order. Run `lake env lean Insertion.lean` from
a matching mathlib environment with the path to this file.

The overlap counts finite points admitting both an exact-three and an
exact-four signed representation. Their union is the radius-four support:
a cancelling pair pads any shorter representation to three or four.
The core overlap is 61056. The core and full basis share all 20 five-term
classes by inclusion and equal counts; the archived five-prefix
classification establishes that each has five distinct labels.

If the seven terms of a three-versus-four equality admit cancellation,
an internal pair leaves a split of a five-term relation entirely in the
core. Cancellation across the equality gives a two-versus-three split
translated by a signed generator. For a single added generator there are
at most 800 new endpoints of this kind: 20 classes, ten splits, two
orientations, and two signs of that generator. Excess beyond 61856 therefore
forces a reduced seven-term equality at a point outside the core overlap.
Its coefficient at the new label is nonzero, since the row is reduced,
contains that label, and its length is smaller than the subgroup order.

The rows supplied by different insertions have different private coordinates.
The 20 independent five-term rows vanish on all these coordinates. This
gives a conditional combined rank of at least 141. The Lean lemmas prove
the finite-set excess and private-coordinate arguments. The existence of
the finite overlap and the five-term classification rely on native counts.
The CSV records cardinalities; it contains no individual seven-term rows.
