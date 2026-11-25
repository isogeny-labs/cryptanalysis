# Coverage of the archived M31 auxiliary basis

The complete bound-89 reciprocal census contains 204,724 coordinates from
6,604 rotation orbits. At identity scale it covers zero of the 32 archived
depth-five structured roots and zero of the 17 lifted factor-base coordinates.
Even permitting any one common nonzero field scale covers at most two
coordinates in either set. The archived random 17-column comparison has
the same maximum. These statements concern membership before imposing
any new lift constraints on the scaled coordinates.

For each archived coordinate x and each census orbit with representative y,
the scale key producing a hit is y^31 / x^31. Distinct census keys yield
distinct scale keys for fixed x. OrbitKey.lean proves this criterion.
Multiplication by two has order 31, so each scale key represents exactly
31 nonzero scales. Counting the sparse scale-key incidences and assigning
the complement to zero hits gives the full distribution. The support is
closed under inversion. The same maximum therefore applies to x mapped to
s/x, via the inverse of the common scale.

Run check.py to regenerate result.json from the pinned Git object. The
result includes explicit maximizing scales and the corresponding input
coordinates. For an independent coordinate-level replay, build the native
pair generator as in ../pair-index/README.md and run direct.py with its
path, using Python with NumPy. This second method expands both orientations
of the 3,302 emitted pairs and counts individual field scales directly.
Both methods agree at every histogram bin, including the zero-hit count.

The benchmark fixture uses a particular public curve and basis. Allowing
all field rescalings here gives an upper bound even for coordinate changes
subject to further restrictions. The bound only applies to these two transform
families and this frozen census and fixture.
