# Integrated M31 command diagnostic

On the frozen public auxiliary/plain M31 fixture target Q=(988441464,
1643383878), run the current `m31-fast` Rust command from Git head
`ed350380e` with coordinate input only, B=256 interval base, signed m2
index, seed 0,1,2, four million query cap and five-second soft online cap.
Build release once outside the timing window. For each seed, start a fresh
process and capture its full JSON certificate, exit code, process wall and
parent-plus-child CPU. Parse phase and pair-index counters, verify the
reported scalar by the command's certificate replay, and preserve incomplete
or failed cells. This is a diagnostic on one frozen public target, not a
speed comparison or a new selection panel. It is intended to locate the
remaining cost after the orbit-hash experiment.
