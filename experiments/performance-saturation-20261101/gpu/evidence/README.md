# GPU saturation evidence

This directory retains immutable transport archives and compact convenience
copies from the performance-saturation GPU studies.  The result archives are
the source of truth; convenience files are byte-identical members or
controller records and are included only to make review possible without
extracting the archive.

## RTX 5090 Nsys-only A/A v7

[`remote-aa-v7`](remote-aa-v7) is the sole frozen v7 allocation.  It completed
all 10 warmups, 60 unprofiled executions, and two post-timing Nsys captures,
then the controller deleted exact pod `wqywy6u8ckeja4` and verified absence.

- protocol canonical SHA-256:
  `4b71152b91077781544520da18b0bafa4a762cf634be4c278867452c11e20c08`
- receipt SHA-256:
  `053e6983c0c0fad8b72d35aaf22d3050763ede83e610e75da821677f3fc6dba7`
- result archive SHA-256:
  `c69fae2f4ded148451c3492174cae6fec1d033e009a4f4e37fd71fdc99c011aa`
- internal 396-entry manifest SHA-256:
  `04885fe46b048a152aa0cd2bcffa9de46c2386dcc8a6f8a532f68367ea39a6fd`
- rows SHA-256:
  `91dd95bf0528154f5a9e0c7f28697f4c79ad415130c5ca95ba5b623764e1f7b8`

Every archive member and its receipt size/hash binding was independently
verified.  The frozen outcome is `aa_calibration_admissible`; this is a
byte-identical A/A calibration and profiler baseline, not an optimization or
speedup result.  See [`../V7_REPORT.md`](../V7_REPORT.md) and
[`../v7-outcome.json`](../v7-outcome.json).
