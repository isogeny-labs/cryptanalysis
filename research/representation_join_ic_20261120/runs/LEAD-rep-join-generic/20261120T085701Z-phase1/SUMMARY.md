# LEAD-rep-join-generic: phase 1 - **FAIL**

- lead: Representation technique as a generic list join (rep-join, no filter): signed m-list MITM at m = 2..9
- cryptanalysis: `4029af2b8fb0bdda18d5022959bd8c5f4cfbc82b`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 11.98 GiB
- next: record as a measured negative at this phase (lead atlas / dead end); do not promote

- no m beat the baseline arm on every instance of the phase

| cell | m | status | pairs | speed-up (geomean) | 95% CI | lead S / matched rho | peak GiB |
|:--|--:|:--|--:|--:|:--|--:|--:|
| bench-prime-16 | baseline | ok | | 1 | | 10.115 | 0.021 |
| bench-prime-16 | 2 | ok | 6 | 1.000 | [1.000, 1.000] | 10.115 | 0.021 |
| bench-prime-16 | 3 | ok | 6 | 0.825 | [0.771, 0.874] | 12.275 | 0.021 |
| bench-prime-16 | 4 | ok | 6 | 0.793 | [0.756, 0.833] | 12.754 | 0.021 |
| bench-prime-16 | 5 | ok | 6 | 0.749 | [0.715, 0.785] | 13.519 | 0.021 |
| bench-prime-16 | 6 | ok | 6 | 0.757 | [0.714, 0.801] | 13.381 | 0.021 |
| bench-prime-16 | 7 | ok | 6 | 0.766 | [0.715, 0.812] | 13.231 | 0.021 |
| bench-prime-16 | 8 | ok | 6 | 0.788 | [0.752, 0.828] | 12.867 | 0.021 |
| bench-prime-16 | 9 | ok | 6 | 0.747 | [0.713, 0.785] | 13.566 | 0.021 |
| bench-prime-18 | baseline | ok | | 1 | | 12.328 | 0.021 |
| bench-prime-18 | 2 | ok | 6 | 1.000 | [1.000, 1.000] | 12.328 | 0.021 |
| bench-prime-18 | 3 | ok | 6 | 0.759 | [0.734, 0.782] | 16.248 | 0.021 |
| bench-prime-18 | 4 | ok | 6 | 0.759 | [0.724, 0.793] | 16.245 | 0.021 |
| bench-prime-18 | 5 | ok | 6 | 0.749 | [0.709, 0.792] | 16.466 | 0.021 |
| bench-prime-18 | 6 | ok | 6 | 0.753 | [0.707, 0.794] | 16.388 | 0.021 |
| bench-prime-18 | 7 | ok | 6 | 0.728 | [0.709, 0.748] | 16.928 | 0.021 |
| bench-prime-18 | 8 | ok | 6 | 0.746 | [0.712, 0.777] | 16.540 | 0.021 |
| bench-prime-18 | 9 | ok | 6 | 0.735 | [0.711, 0.764] | 16.781 | 0.021 |
| bench-char2-17 | baseline | ok | | 1 | | 8.540 | 0.021 |
| bench-char2-17 | 2 | ok | 6 | 1.000 | [1.000, 1.000] | 8.539 | 0.021 |
| bench-char2-17 | 3 | ok | 6 | 0.479 | [0.417, 0.529] | 17.869 | 0.021 |
| bench-char2-17 | 4 | ok | 6 | 0.455 | [0.415, 0.497] | 18.799 | 0.021 |
| bench-char2-17 | 5 | ok | 6 | 0.478 | [0.393, 0.581] | 17.972 | 0.021 |
| bench-char2-17 | 6 | ok | 6 | 0.443 | [0.385, 0.505] | 19.402 | 0.021 |
| bench-char2-17 | 7 | ok | 6 | 0.462 | [0.430, 0.490] | 18.488 | 0.021 |
| bench-char2-17 | 8 | ok | 6 | 0.492 | [0.454, 0.536] | 17.420 | 0.021 |
| bench-char2-17 | 9 | ok | 6 | 0.393 | [0.320, 0.471] | 21.996 | 0.021 |
| bench-char2-21 | baseline | ok | | 1 | | 13.284 | 0.021 |
| bench-char2-21 | 2 | ok | 6 | 1.000 | [1.000, 1.000] | 13.281 | 0.021 |
| bench-char2-21 | 3 | ok | 6 | 0.262 | [0.218, 0.311] | 49.873 | 0.021 |
| bench-char2-21 | 4 | ok | 6 | 0.162 | [0.132, 0.198] | 80.653 | 0.021 |
| bench-char2-21 | 5 | ok | 6 | 0.135 | [0.110, 0.163] | 98.306 | 0.021 |
| bench-char2-21 | 6 | ok | 6 | 0.148 | [0.127, 0.177] | 88.605 | 0.021 |
| bench-char2-21 | 7 | ok | 6 | 0.152 | [0.125, 0.195] | 85.855 | 0.021 |
| bench-char2-21 | 8 | ok | 6 | 0.160 | [0.125, 0.210] | 82.597 | 0.021 |
| bench-char2-21 | 9 | ok | 6 | 0.158 | [0.130, 0.198] | 83.159 | 0.021 |
| bench-koblitz-23 | baseline | ok | | 1 | | 99.869 | 0.021 |
| bench-koblitz-23 | 2 | ok | 6 | 0.023 | [0.023, 0.023] | 4402.923 | 0.143 |
| bench-koblitz-23 | 3 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.006 | 0.143 |
| bench-koblitz-23 | 4 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.035 | 0.143 |
| bench-koblitz-23 | 5 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.082 | 0.143 |
| bench-koblitz-23 | 6 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.105 | 0.143 |
| bench-koblitz-23 | 7 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.156 | 0.143 |
| bench-koblitz-23 | 8 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.175 | 0.143 |
| bench-koblitz-23 | 9 | ok | 6 | 0.023 | [0.023, 0.023] | 4403.231 | 0.143 |

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
