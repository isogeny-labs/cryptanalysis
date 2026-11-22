# Local-search activation on the official ECC2K-130 point

Suppressing Gaussian matrices kept CryptoMiniSat's CCNR local search
active on the exact twelve-leaf adjacent-union formula. The
[raw log](solver.stdout) reports zero admitted matrices and **31 CCNR
rounds**. The one-worker ordinary-point [query](query_result.json)
returned `s INDETERMINATE` after **129.230 seconds** including checked
Sage startup and wrapper work, with **600,915,968 bytes** sampled peak
combined RSS under the 4-GiB cap. The solver reported 122.24 seconds
of its own time. The [custody and activation verifier](verify.py) passes.

The [frozen protocol](query_protocol.json) fixes the same public point
and XCNF as the default and Gaussian arms. Its changed flags set the
maximum number of Gaussian matrices to zero and request CCNR at every
simplification. The exact formula had already passed a full planted
assignment and independent twelve-point Sage replay. This short run
answers the activation question; a full-length arm is the next gate for
ordinary relation recovery. A SAT result would require independent
source-bound curve-group replay before relation use.

Run `python3 verify.py` here to repeat the read-only audit.
