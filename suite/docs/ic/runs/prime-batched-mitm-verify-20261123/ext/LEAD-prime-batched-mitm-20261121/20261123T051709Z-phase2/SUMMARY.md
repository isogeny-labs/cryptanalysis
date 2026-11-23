# LEAD-prime-batched-mitm-20261121: phase 2 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `272d3ec8038cd4e6eba4d8d3ed85981e8a937276`
- registry sha256: `d561f1826ea850e4`; memory ceiling 11.92 GiB
- next: promote: run phase 3

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-28 | baseline | ok | | 1 | | 84.402 | 0.022 |
| bench-prime-28 | 2 | ok | 4 | 4.884 | [4.487, 5.318] | 17.359 | 0.022 |
| bench-prime-28 | 3 | ok | 4 | 3.991 | [3.796, 4.195] | 21.185 | 0.022 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
