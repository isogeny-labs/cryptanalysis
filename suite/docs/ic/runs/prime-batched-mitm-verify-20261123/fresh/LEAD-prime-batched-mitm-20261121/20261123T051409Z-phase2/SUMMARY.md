# LEAD-prime-batched-mitm-20261121: phase 2 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `cb73ed6f2974c80684951b481c1f506c1b7f5e55`
- registry sha256: `312cd1dd6b49ea55`; memory ceiling 11.92 GiB
- next: promote: run phase 3

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-20 | baseline | ok | | 1 | | 17.763 | 0.022 |
| bench-prime-20 | 2 | ok | 8 | 3.070 | [2.748, 3.436] | 5.869 | 0.022 |
| bench-prime-20 | 3 | ok | 8 | 3.026 | [2.827, 3.232] | 5.877 | 0.022 |
| bench-prime-22 | baseline | ok | | 1 | | 25.133 | 0.022 |
| bench-prime-22 | 2 | ok | 8 | 4.591 | [4.503, 4.696] | 5.477 | 0.022 |
| bench-prime-22 | 3 | ok | 8 | 3.601 | [3.445, 3.757] | 6.991 | 0.022 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
