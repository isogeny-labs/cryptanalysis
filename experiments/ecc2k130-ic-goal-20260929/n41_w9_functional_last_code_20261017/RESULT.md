# A one-bit root selector augments the N41 last-pair code equation

The frozen five-pair XCNF now has a guarded functional decoder for its
final eight-bit source code. For regular intermediate reciprocals it
computes both product roots of the last-link linearized quadratic from
`w`; a single branch bit chooses the root, and an exact 41-coordinate
equality ties that product to the source code. The original resultant
and all source and collision constraints remain in the formula.
The exact input is the frozen public point
`(1936680952394, 910597499030)` on `EC1N41Ckb1h7d5e80d3c4d0`;
all five source-pair codes and the intermediate reciprocal are free in
the solver query.

All 284 target-translated source positives and the prior 1,024 field
and 256 reachable controls have nonzero `a(w),b(w)`. On the positive
rows the numerical root choice is 130 for branch zero and 154 for
branch one. Sixteen distributed positive rows passed every added
Boolean gate and clause. The guard covers the remaining field inputs
without excluding their original solutions.
An independent checked-Sage replay agreed on the branch split and the
prior image decisions for all 1,024 field and 256 reachable controls;
its arithmetic interval was 4.027 s with self peak RSS 231,292,928
bytes.

| Formula | Variables | CNF clauses | Native XOR rows | Bytes |
| --- | ---: | ---: | ---: | ---: |
| Frozen five-pair base | 123,218 | 323,673 | 15,811 | 10,757,041 |
| Guarded root extension | 154,004 | 374,981 | 29,507 | 12,253,479 |

The extension itself has **17,089 AND gates**, **51,308 clauses**,
and **13,696 native XOR rows**. Its one-worker build and controls took
**41.823 s** under frozen 120 s and 4 GiB caps, with self peak RSS
**57,114,624 bytes**. The measured source, formula hash, runtime
receipt, and failed first import-path attempt are retained. These are
component results on the current host; the candidate ID remains null
until the complete IC pipeline is specified and measured.

The unpinned public-target solver query used a frozen 590 s solver cap,
600 s parent cap, one worker, and 4 GiB sampled combined RSS. It reached
the parent wall cap at **600.056 s** with status **`BOUNDED_UNKNOWN`**,
5,574 RSS samples, **100,040,704 bytes** sampled peak combined RSS, and
no terminal solver model. The assembled target-dependent stage total
is **645.279 s**: 3.400 s frozen base build, 41.823 s decoder build,
and 600.056 s query. These construction and query intervals came from
their separately frozen runs; the current host lacked benchmark
isolation. This cap result is censored and does not estimate ordinary
relation yield.

`python3 -B verify.py` checks the build and query receipts;
`lean GuardedDecoder.lean` checks the structural preservation theorem.
The decoder's 30,786 extra variables and 65,004 extra constraints did
not pass this N41 query gate. A same-point natural N131 attempt using
this extension is therefore deferred. The next design iteration should
constrain more than the last pair at once: test a compact, exact joint
partial-sum condition on frozen N41 positives and reachable controls,
then measure an unpinned N41 solve before promoting it to N131.
