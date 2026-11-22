# Full local-search arm on the official ECC2K-130 point

The exact twelve-leaf adjacent-union XCNF ran with Gaussian matrices
disabled and CCNR local search active for a full one-worker ordinary
query. The [solver log](solver.stdout) records **104 CCNR rounds** and
zero admitted matrices. The [result](query_result.json) is
`BOUNDED_UNKNOWN` at the **615.064-second parent wall cap**, with no
terminal SAT or UNSAT line. Sampled combined runner and solver RSS
peaked at **756,383,744 bytes** below the 4-GiB cap. The
[custody and activation verifier](verify.py) passes.

The [frozen protocol](query_protocol.json) binds the official point,
source screen, exact formula, checked Sage runtime, solver binary,
one-worker flags and limits, and the earlier 120-second local-search
probe. The [model replay script](replay_sat.py) is ready to check a
future SAT assignment against every clause and native XOR, all twelve
Sage source points, the intermediate sums, the selected cofactor lift,
and the projected prime-subgroup relation. Its
[Sage primitive control](replay_primitives_result.json) passes twelve
planted source charts and the official point's subgroup-order check.
The complete model replay has not run because this attempt produced no
SAT assignment.

The default and ten-matrix Gaussian arms on this same formula and
public point also ended `BOUNDED_UNKNOWN` at their respective
615-second caps. These ordinary-host runs test solver settings; they do
not provide an IC/rho timing ratio. The next encoding screen fixes a
target-independent subset of adjacent-image branch bits to reduce
nonlinear chart cost while retaining enough source choices for the
ordinary relation law. It must pass a full assignment and independent
Sage replay before an unpinned N131 query.

Run `python3 verify.py` from this directory to repeat the read-only
query audit.
