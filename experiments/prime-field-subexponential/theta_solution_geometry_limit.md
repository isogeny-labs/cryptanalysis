# Theta-hit signings show no code or local-search structure

The theta-divisor interpretation leaves open a global recovery strategy: the
rare singular signings might lie in a low-codimension affine slice of the
Boolean cube, form a Hamming-connected cluster, or have an exceptional Walsh
coefficient.  Any of these would provide information unavailable to pointwise
membership probing.

The exact solution sets do not show such structure.  In the largest panel,
the 22 theta-hit signings in \(\mathbf F_2^{11}\):

- affinely span the full 11-dimensional cube;
- have minimum pairwise Hamming distance two and no Hamming-distance-one
  edges, hence 22 singleton components under single-bit flips;
- have maximum nontrivial Walsh magnitude 16 and no perfect nontrivial mode;
  and
- have maximum nonzero ordered-pair XOR multiplicity six.

Across 64 uniformly random 22-point subsets of the same cube, affine rank is
always 11, the median maximum Walsh magnitude is 16, and the XOR-multiplicity
range is two through eight.  The observed theta-hit values therefore sit
inside the matched random range.  The ten-slot panel has one perfect Walsh
mode, but matched random 14-point controls also attain that value and have
affine ranks as low as eight; the feature does not persist at eleven slots.

The smaller panels contain too few hits for affine-span or Fourier tests to be
informative.  These finite controls do not prove pseudorandomness.  They do
exclude the simplest recovery proposals based on solving a few binary linear
constraints, following one-bit neighbors, or selecting an anomalously large
Walsh mode in the tested curve family.

~~~sh
python3 theta_solution_geometry.py |
  cmp - theta_solution_geometry.json
python3 -m py_compile theta_solution_geometry.py
~~~
