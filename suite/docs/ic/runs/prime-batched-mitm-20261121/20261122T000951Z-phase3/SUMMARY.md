# LEAD-prime-batched-mitm-20261121: phase 3 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `225cd56637e7d650831e64b0213d2a3bea180bee`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 11.89 GiB
- next: candidate for the baseline ratchet: freeze a protocol in cryptanalysis (docs/ic/BASELINES.md rules, Tier 1, pcc claim); this harness does not write rows

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-24 | baseline | ok | | 1 | | 53.411 | 0.022 |
| bench-prime-24 | 2 | ok | 8 | 4.859 | [4.376, 5.380] | 11.140 | 0.022 |
| bench-prime-24 | 3 | ok | 8 | 4.650 | [4.437, 4.838] | 11.508 | 0.022 |

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
