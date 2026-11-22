# Frozen ordinary twelve-leaf union query on ECC2K-130

The exact [twelve-leaf adjacent-union formula](ordinary.xcnf) was
submitted to one CryptoMiniSat worker on the frozen public point. The
[query result](query_result.json) is `BOUNDED_UNKNOWN` at the
**615.056-second parent wall cap**, with no terminal SAT or UNSAT line.
Sampled combined runner and solver RSS peaked at **681,639,936 bytes**
under the 4-GiB cap. The worker exited after parent SIGTERM. The
[read-only custody verifier](verify.py) passed.

The [protocol](query_protocol.json) binds the source screen, complete
planted control, independent Sage replay, exact formula and solver binary
hashes, checked Sage runtime, public target, one-worker flags, and caps.
The factor-base source and adjacent-image branch bits were unpinned.
Other solver work was live on this ordinary host, so this wall time is a
bounded query diagnostic, not an isolated IC/rho comparison.

The [raw solver log](solver.stdout) reports that its default Gaussian
row limit left the 10,067-row and 11,172-row XOR matrices unused. A
matched next arm can raise the small-matrix row and column limits while
holding the formula, target, worker count, and resource cap fixed. A SAT
model will require independent source-bound curve-group replay before
it contributes a verified relation.

Run `python3 verify.py` from this directory to recheck custody and the
bounded status.
