# Execution amendment after a censored first run

`PROTOCOL.json` and `run.py` are the frozen first attempt. The checked Sage process remained live at 100% CPU after an observed 104 seconds, with no result rows written. It was interrupted by the operator while multiplying every rational point in every coefficient box. `initial-run.stdout` is empty and `initial-run.stderr.gz` retains the exact `KeyboardInterrupt` traceback bytes. The wrapper shell's final `cat` returned zero; the Python workload itself was interrupted.

`PROTOCOL-v2.json` keeps the curve, point pairs, `n` panel, all `K` cells, falsifiers, and claim boundary. It changes only the enumeration method. `run-v2.py` enumerates the integer scalar image `{a+nb: |a|,|b|≤K}` exactly. The fixed-curve rank-one, trivial-torsion and generator checks establish injectivity of `m↦mP`; the Lean lower-bound theorem supplies the corresponding structural proof for any infinite-order point. Checked Sage also checks the boundary identities on each `nP`. The independent audit recomputes scalar images and thresholds by a separate route.

The censored first attempt remains part of the record and contributes no numeric result.
