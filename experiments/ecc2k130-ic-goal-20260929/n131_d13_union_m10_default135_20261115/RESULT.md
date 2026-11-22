# Same-cap default-matrix control for N131 union XCNF

The default-limit arm on the identical official-point XCNF returned
`s INDETERMINATE` at its 120-second solver limit. The complete
[query result](query_result.json) is `BOUNDED_UNKNOWN`, with **122.651
seconds** parent wall time and **440,336,384 bytes** sampled combined peak
RSS. The exact formula, public point, one worker, 4-GiB cap, and 135-second
parent limit were matched to the ten-matrix admission probe. Both arms ran
on an ordinary shared host.

| Same-cap arm | Solver matrix limits | Matrices reported | Last logged cumulative conflicts | Sampled peak RSS | Status |
| --- | --- | --- | ---: | ---: | --- |
| Default control | defaults | initially 5 small; later 0 | 2.046 million | 440,336,384 B | `BOUNDED_UNKNOWN` |
| Larger-matrix probe | 16,000 rows, 20,000 columns, 10 matrices | initially 10 | 51 thousand | 1,024,475,136 B | `BOUNDED_UNKNOWN` |

The conflict figures are solver diagnostics taken from each arm's last
restart line. Gaussian propagation changes the cost and information per
conflict, so those counts do not measure decomposition progress or a solver
speedup. The larger-matrix arm consumed more sampled memory and remained
within the 4-GiB envelope. A full-length tuned query is the next direct
test for a terminal model on this exact point. Any model requires independent
curve-group replay. Run `python3 verify.py` for the custody check.
