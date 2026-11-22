# W20 root tables show limited BDD compression on four exact 14-bit selector subcubes

The exact W20 pair-output root function was computed on four frozen 14-bit subcubes of its 19-bit source code. They contain **16,548 valid product codes**. A shared-output decision diagram for each 131-bit root used **93,094–94,492 nodes per subcube** under the measured variable order and don't-care rule. Choosing the half-trace root or the smaller encoded root changed each width-14 count by at most 166 nodes. An independent checked-Sage replay recomputed all 4,184 valid codes in prefix zero, matched both node counts with a different recursion, and verified eight source pairs by full group addition.

The source is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, with `y²+xy=x³+1`, fixed W20 seed `898618`, and **132,045** valid unordered source pairs among `2^19` canonical codes. Each valid code selects one source pair. In the standard reciprocal output chart `a=1/x(P+Q)`, its two possible coordinate roots satisfy `C*a²+p*a+h²=0`, where `h=halftrace(seed_coordinate)`, `C=1+h²`, and `p=x(x+seed_coordinate)` for the code's source coordinate `x`. The code computes `d=p/C`, `u=halftrace(h²*C/p²)`, and the roots `d*u` and `d*(u+1)`. Both roots are checked against the quadratic. [PROOF_MAP.md](PROOF_MAP.md) maps the root-shift theorem to its Lean proof and records the concrete-field formalization boundary.

The [frozen protocol](protocol.json) selected prefixes `0,8,16,24` in the high five code bits and widths `8,10,12,14` in the low bits before measurement. Invalid codes are don't-care leaves. Nodes are shared across all 131 output bits within one subcube; the four subcubes are counted separately. This is a component measurement with `candidate_id: null`.

| High-five-bit prefix | Valid codes at width 14 | Half-trace root nodes | Smaller-root nodes |
| ---: | ---: | ---: | ---: |
| 0 | 4,184 | 94,470 | 94,492 |
| 8 | 4,126 | 94,373 | 94,355 |
| 16 | 4,121 | 93,961 | 93,897 |
| 24 | 4,117 | 93,260 | 93,094 |

The 16-row [result](result.json) also records widths 8, 10, and 12. The width-14 counts grow from roughly 2,000 nodes at width 8 and roughly 26,000 at width 12 as more valid codes enter each subcube. The full-domain source-validity BDD has 44,131 nodes, so even one measured root subcube exceeds that simpler membership diagram. The checked-Sage screen completed its computation in 100.061 seconds with 300.2 MB sampled process RSS under a 180-second/4-GiB cap; the [independent audit](audit_result.json) took 63.325 seconds and sampled 320.3 MB. These are exploratory component timings on an unisolated host. The repository's checked [Sage runtime receipt](sage_runtime_info.json) was saved before both jobs.

The screen covers one eighth of the 19-bit code domain. It does **not** measure the full 19-bit root diagram, a seven-slot Boolean circuit, or solver search. Variable order, don't-care completion, and cross-prefix sharing may change the full size. The measured branch convention barely changes size at width 14, so switching roots alone offers no evident compression in this representation. The next method gate should retain the exact direct-parity source circuit as a baseline and test an asymmetric target link that eliminates one pair-output coordinate while leaving the other code and output free. That experiment must compare complete formula size, witness satisfaction, and unpinned N41 search before any N131 ordinary-point query.

Run [verify.py](verify.py) for source hashes, caps, all recorded subcube rows, audit agreement, and the checked runtime status.
