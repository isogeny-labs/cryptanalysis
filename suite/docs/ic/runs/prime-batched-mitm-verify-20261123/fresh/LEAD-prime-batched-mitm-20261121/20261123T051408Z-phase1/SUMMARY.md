# LEAD-prime-batched-mitm-20261121: phase 1 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `cb73ed6f2974c80684951b481c1f506c1b7f5e55`
- registry sha256: `312cd1dd6b49ea55`; memory ceiling 11.94 GiB
- next: promote: run phase 2

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-16 | baseline | ok | | 1 | | 13.562 | 0.022 |
| bench-prime-16 | 2 | ok | 6 | 2.070 | [2.003, 2.154] | 6.558 | 0.022 |
| bench-prime-16 | 3 | ok | 6 | 1.693 | [1.510, 1.852] | 8.062 | 0.022 |
| bench-prime-18 | baseline | ok | | 1 | | 18.113 | 0.022 |
| bench-prime-18 | 2 | ok | 6 | 2.723 | [2.576, 2.898] | 6.679 | 0.022 |
| bench-prime-18 | 3 | ok | 6 | 2.094 | [1.887, 2.302] | 8.691 | 0.022 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
