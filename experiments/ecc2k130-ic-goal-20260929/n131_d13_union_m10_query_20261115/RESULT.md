# Frozen ordinary ten-leaf union query on the ECC2K-130 point

The exact [ten-leaf adjacent-union formula](ordinary.xcnf) was submitted
to one CryptoMiniSat worker on the frozen public ECC2K-130 point. The
[query result](query_result.json) is `BOUNDED_UNKNOWN`: the parent stopped
the worker at **615.048 seconds** without a terminal SAT line. Sampled
combined runner and solver RSS peaked at **647,806,976 bytes**. The worker
exited by SIGTERM at the frozen parent cap; no relation row entered the IC
collector. The raw [solver output](solver.stdout), empty stderr, exact
binary hash, flags, formula hash, and checked Sage runtime are bound by the
[protocol](query_protocol.json).

This was a one-worker, 4-GiB ordinary-host query. Other solver processes
were live on the host, so its wall time is a bounded attempt status rather
than a controlled IC/rho performance measurement. The factor-base source
bits and all ten adjacent-image branch bits were free. The earlier planted
assignment checked the circuit, while this query tested the actual public
target without pins.

The solver's log repeatedly reports XOR matrices of roughly 11,172 rows
and 15,349 columns as unused because the row limit was exceeded; it reports
**zero matrices in use** near the cap. This is a concrete solver-configuration
lead. A paired arm can raise the permitted matrix dimensions on the same
formula, target, worker count, 4-GiB cap, and 615-second parent limit. The
falsifier is failure to activate the matrices or a bounded run with no
verified model under that arm. Any SAT model must be decoded to exact
curve points and replayed against the same public target before use.

Run `python3 verify.py` from this directory for the read-only custody check.
