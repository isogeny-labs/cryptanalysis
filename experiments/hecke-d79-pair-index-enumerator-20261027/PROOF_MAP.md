# Proof map

| Claim | Lean declaration or executable check | Exact hypotheses and status |
| --- | --- | --- |
| A two-term signed support cancels iff the second value is the negative of the first | `PairIndexCancellation.two_cancel_iff` | Arbitrary additive commutative group; Lean build passed |
| A leading signed pair and a later singleton cancel iff the singleton bucket holds the negative leading sum | `PairIndexCancellation.three_cancel_iff` | Arbitrary additive commutative group; Lean build passed |
| Two signed pairs cancel iff the later pair bucket holds the negative leading sum | `PairIndexCancellation.four_cancel_iff` | Arbitrary additive commutative group; Lean build passed |
| Strictly increasing supports of size one through four are enumerated exactly once | Written argument below; `benchmark_sage.py` exact-set comparison | Python index implementation and pinned exhaustive enumerator; all 30 paired replays passed, but the loop implementation is not encoded in Lean |
| Every emitted class row is a curve-group relation | `pair_index.py` group replay, checked against pinned exhaustive output and prior independent Sage audits | Ten sealed D79 classes, 2,003 distinct relation rows per repetition total |

For four distinct ordered source indices `i<j<k<l`, normalize the sign at `i` to +1. The index queries each `i<j` with both signs at `j`. It inserts every signed `k<l` pair into the bucket for its group sum. The Lean four-term identity says a cancellation exists exactly when the bucket key is the negative of the leading-pair sum. The `k>j` guard makes this the unique ordered split of that support. The same leading-pair query checks singleton buckets for ordered triples; two-source and one-source cancellations are checked directly. Conversely, every matched complement sums to zero and is independently verified as a class row. No sign orbit is lost because global negation lets the first sign be fixed to +1.

The Lean kernel audit in `formal/build-output.txt` reports only `propext` for the three algebraic equivalences. The bridge from the Python ordered-loop implementation to the Lean group elements is covered by exact output-set comparison on frozen traces, not a full formalization of Python or elliptic-curve arithmetic. The pinned toolchain and dependency revisions are in `formal/lean-toolchain` and `formal/lake-manifest.json`.
