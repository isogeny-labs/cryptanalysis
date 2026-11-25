# Target-only lifting from a packed M31 smooth-coordinate buffer

Run `sh replay.sh` to compare the published sixteen-chain M31 basis preparation with the same path using one native call for all smooth coordinates. Both paths call m31_lift32 on 32 inputs at a time and return a Python list of ordered (x,y) tuples. The new wrapper reads full blocks directly, pads its last block, writes valid coordinates and ordinates into separate output arrays, and returns their common length.

Each panel measures 128 alternating pairs after eight warmup pairs for each scope. Lift starts with the packed 392-coordinate filter output. Setup regenerates and checks the depth-15 auxiliary fiber, filters the 32768 public coordinates, then constructs the same 195 target points. Both scopes include returned Python objects. All calls compare against the independent ordered reference. The replay also checks lengths 0 through 64 with repeats and edge coordinates.

| Scope | First build, paired wall gain | Fresh build, paired wall gain |
| --- | ---: | ---: |
| Lift and construct Python points | 4.584× | 4.588× |
| Complete public basis preparation | 1.085× | 1.096× |

Compact.lean proves stable chunk concatenation, exclusion of padding and ordered reconstruction from coordinate columns for the logical filter. The existing Ordinate.lean proves the M31 ordinate and sentinel specifications. The FFI and C writes are tested by differential replay.
