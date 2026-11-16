# Native SIMD inverse correctness preparation

One NEW L4CPU4/8GiB900s, apt time, CPU only. Locked default release-j2 build780s
cap; existing walker debug filter180s, vector-full60s, constant60s, framework90s,
vector-inverse90s. Whole900s allocation hard cap wins; no host retry/extension.
Exact published source and source/compiler/binary/environment receipts retained.

175complete witness maps,15synthetic loader controls,5batched-walk tests,
2vector-full,1constant,27framework,3vector-inverse tests; filters overlap and are
not a distinct-test total. Four512state stream comparisons per field: native,
scalar,eager,vector,vector-inverse share frames/group ops and exact coefficients.
Require actual inverse-vector element/batch counts positive in all five fields,
with padding and fallback counters. Direct inverse products cover all accepted
field widths, zero patterns, lengths0..31 and noncanonical rejection; curve-point
API covers exceptions, append/reuse and unsupported-length fallback. Existing
Python checks2560exported states after fetch. No performance result from prep.

The frozen previous binary1026bf74/source25be1116c is a separate timing anchor;
anchor-input.json and anchor-job-metadata.json preserve its exact binding. New
source/binary is compared both against that anchor and its own ordinary inverse
control on fresh targets after source/protocol/input publication. Defaults stay.
