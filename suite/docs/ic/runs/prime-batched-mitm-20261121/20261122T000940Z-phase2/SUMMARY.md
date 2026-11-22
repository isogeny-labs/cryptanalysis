# LEAD-prime-batched-mitm-20261121: phase 2 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `225cd56637e7d650831e64b0213d2a3bea180bee`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 11.89 GiB
- next: promote: run phase 3

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-20 | baseline | ok | | 1 | | 22.567 | 0.021 |
| bench-prime-20 | 2 | ok | 8 | 2.910 | [2.764, 3.083] | 7.791 | 0.021 |
| bench-prime-20 | 3 | ok | 8 | 2.677 | [2.571, 2.775] | 8.439 | 0.021 |
| bench-prime-22 | baseline | ok | | 1 | | 27.101 | 0.021 |
| bench-prime-22 | 2 | ok | 8 | 3.708 | [3.540, 3.898] | 7.336 | 0.021 |
| bench-prime-22 | 3 | ok | 8 | 3.676 | [3.482, 3.853] | 7.391 | 0.021 |

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
