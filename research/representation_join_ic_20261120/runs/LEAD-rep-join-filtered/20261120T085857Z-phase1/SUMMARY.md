# LEAD-rep-join-filtered: phase 1 - **FAIL**

- lead: Representation technique as a generic list join (rep-join, abscissa filter density 1/4): signed m-list MITM at m = 2..9
- cryptanalysis: `4029af2b8fb0bdda18d5022959bd8c5f4cfbc82b`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 11.98 GiB
- next: record as a measured negative at this phase (lead atlas / dead end); do not promote

- no m beat the baseline arm on every instance of the phase

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-16 | baseline | ok | | 1 | | 10.115 | 0.021 |
| bench-prime-16 | 2 | ok | 6 | 0.740 | [0.646, 0.859] | 13.846 | 0.021 |
| bench-prime-16 | 3 | ok | 6 | 0.584 | [0.565, 0.609] | 17.322 | 0.021 |
| bench-prime-16 | 4 | ok | 6 | 0.571 | [0.529, 0.616] | 17.737 | 0.021 |
| bench-prime-16 | 5 | ok | 6 | 0.523 | [0.492, 0.569] | 19.394 | 0.021 |
| bench-prime-16 | 6 | ok | 6 | 0.536 | [0.505, 0.572] | 18.889 | 0.021 |
| bench-prime-16 | 7 | ok | 6 | 0.545 | [0.517, 0.571] | 18.579 | 0.021 |
| bench-prime-16 | 8 | ok | 6 | 0.562 | [0.514, 0.601] | 18.088 | 0.021 |
| bench-prime-16 | 9 | ok | 6 | 0.542 | [0.512, 0.577] | 18.676 | 0.021 |
| bench-prime-18 | baseline | ok | | 1 | | 12.328 | 0.021 |
| bench-prime-18 | 2 | ok | 6 | 0.789 | [0.721, 0.879] | 15.717 | 0.021 |
| bench-prime-18 | 3 | ok | 6 | 0.541 | [0.522, 0.558] | 22.781 | 0.021 |
| bench-prime-18 | 4 | ok | 6 | 0.519 | [0.499, 0.538] | 23.789 | 0.021 |
| bench-prime-18 | 5 | ok | 6 | 0.507 | [0.490, 0.525] | 24.303 | 0.021 |
| bench-prime-18 | 6 | ok | 6 | 0.544 | [0.523, 0.572] | 22.690 | 0.021 |
| bench-prime-18 | 7 | ok | 6 | 0.513 | [0.503, 0.523] | 24.060 | 0.021 |
| bench-prime-18 | 8 | ok | 6 | 0.546 | [0.512, 0.585] | 22.597 | 0.021 |
| bench-prime-18 | 9 | ok | 6 | 0.527 | [0.514, 0.540] | 23.406 | 0.021 |
| bench-char2-17 | baseline | ok | | 1 | | 8.543 | 0.021 |
| bench-char2-17 | 2 | ok | 6 | 0.483 | [0.392, 0.612] | 17.911 | 0.021 |
| bench-char2-17 | 3 | ok | 6 | 0.296 | [0.257, 0.341] | 28.885 | 0.021 |
| bench-char2-17 | 4 | ok | 6 | 0.280 | [0.250, 0.315] | 30.436 | 0.021 |
| bench-char2-17 | 5 | ok | 6 | 0.257 | [0.223, 0.303] | 33.267 | 0.021 |
| bench-char2-17 | 6 | ok | 6 | 0.241 | [0.219, 0.265] | 35.493 | 0.021 |
| bench-char2-17 | 7 | ok | 6 | 0.260 | [0.245, 0.278] | 32.827 | 0.021 |
| bench-char2-17 | 8 | ok | 6 | 0.283 | [0.247, 0.327] | 30.508 | 0.021 |
| bench-char2-17 | 9 | ok | 6 | 0.286 | [0.231, 0.340] | 30.339 | 0.021 |
| bench-char2-21 | baseline | ok | | 1 | | 13.280 | 0.021 |
| bench-char2-21 | 2 | ok | 6 | 0.407 | [0.297, 0.542] | 33.207 | 0.021 |
| bench-char2-21 | 3 | ok | 6 | 0.149 | [0.119, 0.180] | 89.314 | 0.021 |
| bench-char2-21 | 4 | ok | 6 | 0.099 | [0.076, 0.128] | 133.140 | 0.021 |
| bench-char2-21 | 5 | ok | 6 | 0.093 | [0.074, 0.118] | 142.789 | 0.021 |
| bench-char2-21 | 6 | ok | 6 | 0.100 | [0.088, 0.113] | 131.050 | 0.021 |
| bench-char2-21 | 7 | ok | 6 | 0.088 | [0.072, 0.110] | 147.475 | 0.021 |
| bench-char2-21 | 8 | ok | 6 | 0.110 | [0.094, 0.135] | 119.074 | 0.021 |
| bench-char2-21 | 9 | ok | 6 | 0.106 | [0.088, 0.129] | 124.005 | 0.021 |
| bench-koblitz-23 | baseline | ok | | 1 | | 99.869 | 0.021 |
| bench-koblitz-23 | 2 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.074 | 0.144 |
| bench-koblitz-23 | 3 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.208 | 0.144 |
| bench-koblitz-23 | 4 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.208 | 0.143 |
| bench-koblitz-23 | 5 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.292 | 0.143 |
| bench-koblitz-23 | 6 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.280 | 0.143 |
| bench-koblitz-23 | 7 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.368 | 0.143 |
| bench-koblitz-23 | 8 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.351 | 0.144 |
| bench-koblitz-23 | 9 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.444 | 0.143 |

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
