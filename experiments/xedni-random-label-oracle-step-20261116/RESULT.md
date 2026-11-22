# One fresh group-oracle output preserves random-label coupling

**Theorem.** If two collision-free public group traces have the same
number of observed elements, and the next oracle operation returns a
previously unseen element in both executions, there is a bijection of
random bijective encodings that preserves every earlier visible label
and gives the new elements the same label. The checked Lean theorem
applies this to an addition of the same two previously observed indices.
It also proves equal encoding counts for every event on the complete
old-plus-new label tuple.

The result is a one-step extension of the fixed-trace coupling in the
parent PR. It supplies the fresh-output case needed for an adaptive
generic-oracle argument: an algorithm seeing the paired labels chooses
the same next indices, while the new random encoding remains
indistinguishable until a collision. The formal statement requires
freshness in both executions. A full generic-group bound additionally
needs induction across arbitrary commands and a first-collision count.

## Exhaustive transition census

The frozen five-element additive-group experiment enumerates every
one of the 120 bijective encodings. It starts from matched injective
traces x=(0,1,2) and y=(0,2,3). The same addition command doubles
the last observed element, extending them to x=(0,1,2,4) and
y=(0,2,3,1), both injective. An explicit group permutation pairs
all 120 encodings and preserves all four visible labels.

| Trace pair | Distinct visible tuples on x | On y | Histogram equality |
| --- | ---: | ---: | --- |
| Initial three elements | 60 | 60 | yes |
| Fresh doubled-last output | 120 | 120 | yes |
| Boundary addition of second and third elements | 120 | 60 | no |

For the boundary command, x adds 1+2=3, which is fresh, while y adds
2+3=0, repeating the first observed element. Its unequal histograms
show the exact failure mode when the freshness premise is dropped.
The independent audit regenerates all six complete histograms,
the addition outputs, the 120-encoding pairing and the tuple counts.

The theorem and census use uniformly random bijective labels, as in
[Shoup's generic-group model](https://www.shoup.net/papers/dlbounds1.pdf).
They do not treat concrete curve coordinates as random labels.

Run python3 run.py and python3 audit.py; from formal/, run lake build
OracleStep. The parent Lean dependency, module, protocol, complete
histograms, independent audit, and build receipt are sealed.
python3 verify.py checks the packet.
