# M31 public pair-table construction

Run `python3 replay.py > fresh.csv` from this directory on a little-endian host with Git,
Python 3.8 or newer and a C++17 compiler. The runner reads the frozen public fixtures and
arithmetic header from Git, regenerates reference tables with Python affine arithmetic,
and checks four SHA-256 digests before timing the native executable.

Each process starts with the 500 public basis points in memory. Timing includes curve
checks, signed point expansion, hash table allocation, all pair additions, orientation
selection and insertion. Both layouts visit 500,000 finite signed pair sums. The compact
table keeps the even-y member of each sign pair. After timing, every key and its selected
pair indices are checked against the independent reference. File I/O, reference checks,
table destruction, basis generation and relation search fall outside the clock.

The supplied replay.csv was measured on local arm64 with Apple clang 21.0.0 at -O3.
Each basis has 24 paired rounds, split equally between the two execution orders.
The median within-round full/compact build ratio was 2.248 for auxiliary and 1.898 for
plain. Compact won 21 and 20 rounds respectively. These timings measure table construction.
