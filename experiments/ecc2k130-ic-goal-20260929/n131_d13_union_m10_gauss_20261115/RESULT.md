# N131 ten-leaf XOR-matrix admission probe

Raising CryptoMiniSat's Gaussian matrix limits on the same frozen official
point and exact ten-leaf XCNF admitted **10 matrices** in the solver's
initial pass. The [raw log](solver.stdout) records this directly. The
default-limit 615-second run initially admitted five small matrices and
later reported zero at its subsequent matrix rebuilds. This probe used
`--maxmatrixrows=16000 --maxmatrixcols=20000 --maxnummatrices=10`, one
worker, and the same 4-GiB sampled RSS cap.

The [probe result](query_result.json) is `BOUNDED_UNKNOWN`: it reached the
frozen **135.068-second parent cap** without a terminal SAT line. Sampled
combined RSS peaked at **1,024,475,136 bytes**. The larger matrices entered
the solver, but matrix admission alone did not produce a verified relation
within this short cap. These measurements are ordinary-host solver
diagnostics, with other workloads present; they do not establish a wall-time
speedup over the default arm.

The next controlled solver screen is a same-cap default-limit replay paired
with this 135-second arm, recording conflicts and matrix use under the same
host/resource envelope. A full 600-second tuned query should be promoted
only if that screen supplies a concrete search-progress or solve advantage.
Run `python3 verify.py` here for the custody check.
