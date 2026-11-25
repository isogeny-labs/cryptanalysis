# Smooth reciprocal siblings inside the archived depth-five fiber

At each archived two-isogeny step put u = x-r. The two distinct coordinates
with the same parent u+A+B/u are u and B/u in this shifted coordinate.
Fiber.lean proves the parent criterion over a field with nonzero denominators.
It also proves that after a common scaling s the product of their orbit keys
is (s²B)^31. Hence the keys are reciprocal precisely when s²B belongs to the
31-element rotation subgroup. In this fixture each B has two square roots,
and all 31 rotations are squares. This gives exactly 62 compatible scales
per level. Using one of the two square roots of 1/B and changing its sign
represents the two scale orbits under rotation.

The bound-89 census captures zero complete sibling pairs at compatible scales
at all five levels. Allowing unconstrained nonzero scalings captures at most
one complete pair at levels 1 through 3 and zero at the last two levels.
The audit follows the 32 archived roots through all five shifted maps and
checks the final coordinate against the manifest.

For an eligible nonsquare coordinate the minimum smoothness bound for its
orbit is the minimum, over all 31 rotations, of the largest odd prime factor.
Removing a power of two from a representative only moves it within the orbit.
Both orbit directions must qualify and their keys must differ. `thresholds.json` reports the first bound and an attaining scale and pair at
each level. The minima in chain order are 331, 211, 1423, 811 and 2789.
These are thresholds for at least one compatible pair at each level.

Replay from this directory with Python 3:

```sh
python3 check.py /absolute/path/to/native-pairs-helper | diff - result.json
python3 direct.py
python3 threshold.py | diff - thresholds.json
python3 enumeration_size.py | diff - sizes.txt
```

The helper is built from native-pairs/pairs.cpp in the parent census.
The NumPy replay groups by parent and counts individual field scales.
The key-based replay groups by sibling involution and counts scale classes.
The candidate counts in sizes.txt include all positive odd smooth integers
below the modulus, prior to character filtering, orbit merging or lift tests.
They measure enumeration volume. No timings at expanded bounds were taken.
