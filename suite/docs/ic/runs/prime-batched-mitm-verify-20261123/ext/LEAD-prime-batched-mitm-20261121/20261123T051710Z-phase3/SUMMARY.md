# LEAD-prime-batched-mitm-20261121: phase 3 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `272d3ec8038cd4e6eba4d8d3ed85981e8a937276`
- registry sha256: `d561f1826ea850e4`; memory ceiling 11.91 GiB
- next: candidate for the baseline ratchet: freeze a protocol in cryptanalysis (docs/ic/BASELINES.md rules, Tier 1, pcc claim); this harness does not write rows

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-32 | baseline | ok | | 1 | | 114.756 | 0.096 |
| bench-prime-32 | 2 | ok | 3 | 3.909 | [3.683, 4.284] | 29.466 | 0.065 |
| bench-prime-32 | 3 | ok | 3 | 2.609 | [2.417, 2.850] | 44.023 | 0.062 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
