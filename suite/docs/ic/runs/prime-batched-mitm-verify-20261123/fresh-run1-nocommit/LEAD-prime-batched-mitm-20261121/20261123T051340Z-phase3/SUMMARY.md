# LEAD-prime-batched-mitm-20261121: phase 3 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `None`
- registry sha256: `312cd1dd6b49ea55`; memory ceiling 11.92 GiB
- next: candidate for the baseline ratchet: freeze a protocol in cryptanalysis (docs/ic/BASELINES.md rules, Tier 1, pcc claim); this harness does not write rows

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-24 | baseline | ok | | 1 | | 33.861 | 0.022 |
| bench-prime-24 | 2 | ok | 8 | 4.264 | [3.967, 4.548] | 7.997 | 0.022 |
| bench-prime-24 | 3 | ok | 8 | 4.374 | [4.227, 4.531] | 7.747 | 0.022 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
