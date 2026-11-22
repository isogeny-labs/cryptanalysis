# Symbolic public-group collision theorem and complete curve replay

**Theorem.** For a fixed collection of `n` public group expressions made by
adding and scaling `G` and `Q=wG`, each expression has an affine scalar form
`a w+b`. Two distinct forms with the same slope cannot collide. A collision
between different slopes determines exactly one candidate scalar. The checked
Lean theorem identifies the complete collision target set with the image of
those pair candidates, and bounds its size by the number of informative
pairs, hence by `n²`.

This is a formal xedni control for fixed symbolic public-group computations.
It instantiates the familiar collision mechanism behind the generic-group
lower-bound literature; [Shoup's original paper](https://www.shoup.net/papers/dlbounds1.pdf)
analyzes adaptive generic algorithms with random encodings. The present
theorem proves a narrower fixed-trace statement. Point-coordinate access,
random-encoding coupling, and adaptively selected forms need separate
arguments before a claim about a full algorithm follows.

## Complete p=313 public-group experiment

The frozen schedule stores 36 points on `E/F₃₁₃: y²=x³−x−2`:
`Q+iG` for `i=0..17` and `(18j)G` for `j=0..17`, with `G=(2,2)` of order
331 and `Q=wG`. The producer enumerated all 331 target scalars and tested
all 18×18 cross-pair equalities with actual elliptic-curve operations. The
independent modular audit reconstructs every collision and first collision.

| Exact metric | Result |
| --- | ---: |
| Target scalars enumerated | 331 |
| Stored public expressions | 36 |
| Informative cross pairs | 324 |
| Distinct candidate scalars | 324 |
| Targets with a collision | 324 |
| Group equality tests across the census | 107,244 |

The candidates are `w=18j−i mod 331`; they are distinct for the selected
`0≤i,j<18`. Each yields one verified group equality. Seven scalars have no
collision in this schedule. The equality-test count records the exhaustive
all-target census, not an optimized online baby-step/giant-step runtime.
The p=313 generator has an exact-order Lean certificate in the parent
public-first PR. This replay is a correctness and collision-count control,
with no matched rho timing claim.

## Reproduce

The checked Sage launcher saved `sage-runtime-info.json` before running
`run_sage.py`. Run the producer with
`/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run_sage.py`,
then `python3 audit.py`; run `lake build SymbolicCollision` from `formal/`.
`python3 verify.py` checks the sealed files, independent audit, and Lean
receipt. The next proof step is a coupling bound for equality-adaptive
symbolic traces, followed by an explicit accounting of any coordinate-based
selection mechanism.
