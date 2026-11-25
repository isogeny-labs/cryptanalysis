# LEAD-prime-batched-mitm-20261121: phase 1 - **PASS**

- lead: Prime-field MITM prepared and probed in batches (x-only sum/difference per inversion, Montgomery batch inversion, native pricing)
- cryptanalysis: `225cd56637e7d650831e64b0213d2a3bea180bee`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 11.89 GiB
- next: promote: run phase 2

- lower 95% bound of the paired speed-up above 1 on every instance of the phase at m in ['2', '3']

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-16 | baseline | ok | | 1 | | 10.115 | 0.021 |
| bench-prime-16 | 2 | ok | 6 | 1.983 | [1.865, 2.092] | 5.121 | 0.021 |
| bench-prime-16 | 3 | ok | 6 | 1.669 | [1.562, 1.776] | 6.072 | 0.021 |
| bench-prime-18 | baseline | ok | | 1 | | 12.328 | 0.021 |
| bench-prime-18 | 2 | ok | 6 | 2.959 | [2.677, 3.257] | 4.209 | 0.021 |
| bench-prime-18 | 3 | ok | 6 | 2.135 | [2.013, 2.235] | 5.785 | 0.021 |

Not run (the lead's plug-in does not take this summand count): m in ['4', '5', '6', '7', '8', '9'].

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
