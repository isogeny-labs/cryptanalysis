# LEAD-prime-batched-mitm-20261121: phase 1 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `272d3ec8038cd4e6eba4d8d3ed85981e8a937276`
- registry sha256: `d561f1826ea850e4`; memory ceiling 11.95 GiB
- next: promote: run phase 2

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-24 | baseline | ok | | 1 | | 30.911 | 0.022 |
| bench-prime-24 | 2 | ok | 8 | 4.568 | [4.366, 4.730] | 6.781 | 0.022 |
| bench-prime-24 | 3 | ok | 8 | 4.328 | [4.123, 4.513] | 7.155 | 0.022 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
