# Exact fixed-terminal W18 root filter at N131

The W18 half-trace pair law yields a degree-four polynomial in the first pair's product when the terminal pair and four-point output are fixed. On the constructed four-point control, its roots intersect the complete 33,188-product admissible source in exactly one product, 3328 (code 4). An independent bit-field implementation scanned every source product and reproduced that intersection, the two pair equations, upper S3 equation, and the raw elliptic-curve point sum. This provides an exact, source-aware filter for a fixed terminal state and a specified upper-S3 output.

## Method and frozen inputs

Curve `EC1N131Ckb1heb5f1998f20b` uses GF(2^131) with modulus `t^131+t^13+t^2+t+1` and `y^2+xy=x^3+1`. The terminal state is pool state 0, sign pair `(0,0)`, masks `(10,222)`, at rotation 128. The first free pair is at rotation 0. Terminal folded columns are excluded from the first-pair source; 33,188 distinct product values remain. The checked Sage runtime is saved in `sage_runtime_info.json`. The producer was launched through the repository `./sage -python` launcher with one worker, a 600-second parent cap, 120 seconds per case, and a 4 GiB RSS cap. The independent scan used pure Python bit-field arithmetic, one worker, 120 seconds per case, and the same RSS cap. Input and source SHA-256 hashes are frozen in `protocol_v2.json` and `audit_protocol.json`; the latter binds `result_v2.json` as input. Candidate ID remains null because this is a component experiment, not a complete IC pipeline.

Write `h²=HT(w)^2`, where `w=u²+u` is the fixed-seed source coordinate, and let `k=1+h²`. For a first-pair product `p` and reciprocal sum `c`, the pair equation is `k c²+p c+h²=0`. Rotate the terminal coefficients by Frobenius^128, giving `ell=1+h'²`, product `q`, and `ell d²+q d+h'²=0`. The upper S3 equation for the fixed four-point reciprocal `z` is `(cdz)²+cdz+(c+d+z)²=0`. Eliminating `c,d` using the two quadratics produces the degree-four polynomial in `p` evaluated by `run_v2.py` and independently by `audit.py`.

| Frozen output `z` | Producer field roots | Source products, producer / independent scan | Producer query | Independent full scan |
| --- | ---: | ---: | ---: | ---: |
| Constructed four-point control | 4 | 1 / 1: `(3328, code 4)` | 2.312 s | 10.971 s |
| Field control `z=3` | 4 | 0 / 0 | 2.180 s | 10.941 s |
| Public target residual after subtracting terminal state 0 | 4 | 0 / 0 | 3.288 s | 10.876 s |

The public residual still contains eight pairs. Its zero in this table describes only the fixed-terminal **two-pair** query, not the full nine-pair relation problem. All timings are exploratory on a contended host; producer RSS peaked at 267,419,648 bytes and audit RSS at 49,233,920 bytes. The producer's per-query interval covers polynomial construction and field root extraction after source construction. The independent interval covers construction of the polynomial and evaluation at all 33,188 source values. Neither is a complete online target interval.

## Failure receipt and replay

`run.py`/`protocol.json` attempted to reuse an archived 266-term resultant from a different source law. It failed the constructed positive control and is retained as `failure_v1.json` with `PRODUCER_FAILURE` and no scientific decision. The corrected W18 half-trace model is in `run_v2.py`/`protocol_v2.json`; its saved result and the independent scan are in `result_v2.json` and `audit.json`. Run `python3 -B verify.py` to check the frozen hashes, caps, statuses, all three root intersections, and empty error streams. Recomputing the producer requires the checked repository Sage launcher; recomputing the independent scan requires `python3 -B audit.py` and its frozen protocol.

The next experiment must generate or constrain a four-point output from the **other seven pairs and the public target**, then apply this degree-four filter before enumerating the full combination family. A control should include the constructed nine-pair fixture, followed by the frozen public point under the same cap. The filter's exactness is established for a specified output; its usefulness depends on producing such outputs cheaply enough.
