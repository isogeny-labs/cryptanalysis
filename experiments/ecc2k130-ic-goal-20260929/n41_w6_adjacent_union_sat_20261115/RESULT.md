# Exact N41 adjacent-union SAT source gate

An exact six-bit lookup for each of the six adjacent-union source positions
was combined with a balanced five-link S3 native-XOR circuit. The public
N41 target's independently verified six-point relation satisfies the full
unconstrained formula: **17,283 variables, 61,345 clauses, 1,703 XOR rows,
and 15,129 AND gates**. The six leaf selectors remain free in the solver
query. The formula is 1,243,040 bytes.

The source is the 768-point, 26-log-column N41 union in the preceding
six-slot result, on `y²+xy=x³+1` over `GF(2)[t]/(t^41+t^3+1)`. Each slot
contains 64 distinct x-coordinates, 32 from the original base and 32
from `P+tau(P)`, with two signs per x. The exact lookup constrains each
six-bit selector to its position's reciprocal x-coordinate. The balanced
S3 chain represents the supplied public point
`(1458168294740,1672312028033)`. The complete-assignment control uses
row IDs `[91,0,19,19,10,15]` only to validate the circuit; they are not
fixed in `ordinary.xcnf`.

The first build stopped during Python import because a historical helper
path no longer exists in the main crypto checkout. Its source, protocol,
stderr, and `PRODUCER_FAILURE_IMPORT` status are retained. The amended
[protocol](protocol_v2.json) pins a local helper snapshot and was frozen
before the successful build. The checked local Sage runtime receipt is
retained with both build records.

One ordinary public query used CryptoMiniSat with one worker, a 120-second
solver flag, 135-second parent wall cap, and 4-GiB combined RSS cap. The
[query receipt](query_result.json) records **`BOUNDED_UNKNOWN`** after the
parent cap, with no terminal SAT line, 135.101 seconds of runner wall time,
and 556,515,328 sampled peak combined RSS bytes. Raw stdout and stderr are
preserved. A first attempt to launch the runner with system Python stopped
before solver startup because `psutil` was unavailable there; the actual
frozen query used the checked repository Sage launcher.

The positive assignment establishes exact source and S3 encoding for the
known public relation. The bounded ordinary SAT status measures this
solver/encoding gate. Next, compare a lower-cost leaf membership circuit
or a target-conditioned pair filter against the same frozen source, keeping
the same public query and control; promote to an N131 ten-leaf solver arm
only after an unpinned ordinary N41 model is independently replayed.
