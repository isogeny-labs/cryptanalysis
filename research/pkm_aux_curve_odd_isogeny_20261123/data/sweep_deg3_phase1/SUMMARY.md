# pkm-iso-deg3: phase 1 - **FAIL**

- lead: PKM auxiliary-curve tower with Degree-3 Vélu levels (--iso-degrees 3)
- cryptanalysis: `None`
- registry sha256: `e840213ad5cfcc8c`; memory ceiling 12.0 GiB
- next: record as a measured negative at this phase (lead atlas / dead end); do not promote

- lead lost cells the reference completed at ['pkm-m2', 'pkm-m3', 'pkm-m4']

| m | status | ref max N | lead max N | ref peak GiB | lead peak GiB | ref run | lead run | pairs | speed-up | 95% CI |
|--:|:--|--:|--:|--:|--:|:--|:--|--:|--:|:--|
| 2 | ok | 16 | 16 | 2.459 | 4.897 | ok | ok | 116 | 0.728 | [0.642, 0.815] |
| 3 | ok | 12 | 12 | 6.019 | 4.698 | oom_killed | ok | 36 | 0.684 | [0.506, 0.881] |
| 4 | ok | 8 | 8 | 2.524 | 2.261 | ok | ok | 12 | 1.000 | [1.000, 1.000] |
| 5 | ok | - | - | 3.404 | 6.033 | ok | oom_killed | 0 | - | - |
| 6 | skipped | - | - | - | - | - | - | - | - | - |
| 7 | skipped | - | - | - | - | - | - | - | - | - |
| 8 | skipped | - | - | - | - | - | - | - | - | - |
| 9 | skipped | - | - | - | - | - | - | - | - | - |

`oom_killed` / `timeout` are resource limits, not negative results (PROTOCOL.md section 5). Ratios are paired within this run only.
