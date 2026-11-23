# Four-lane M31 batch inversion

The public depth-15 setup regenerates and checks the auxiliary fiber, filters its signed smooth coordinates, and returns 195 ordered points. Four interleaved prefix products shorten the serial dependency in the affine layer expansion and the reciprocal completion. Each lane inverts its own final product. Both kernels also replace the constant remainder operator with one Mersenne fold. Calls below 64 entries and irregular lengths use the existing scalar routine.

Run `sh replay.sh > panel.csv` on the arm64 build host. Each of the 24 possible four-arm orders appears once in warmup and four times during measurement. Arm 0 uses the scalar control in both phases, arm 1 changes layer expansion, arm 2 changes reciprocal completion, and arm 3 changes both. The Python runner checks every timed output against the ordered reference and checks the reference digest. Timings include basis construction after library loading. The first panel used the previously built lift library. The second rebuilt every library from source.

The paired median wall speedups of arm 3 over arm 0 were 1.248 and 1.242. The two panels are separate. Both arithmetic changes are present within each changed kernel, so the phase comparison leaves their individual contributions unresolved. Stripe.lean proves the four-column reverse recovery and slot order under nonzero field inputs. The adjacent M31Reduction.lean verifies the Mersenne fold. The correspondence to the compiled C is tested on the fixture.

## Reduction and number of product chains

Run `sh replay.sh factorial` to reproduce the matched-source comparison. Arm 0 uses one chain and the C remainder operator, arm 1 uses one chain and the Mersenne fold, arm 2 uses four chains and the remainder operator, and arm 3 uses four chains and the fold. Short and irregular calls use the same original fallback. In factorial.csv the median paired gain from switching to four chains was 1.199× with remainder and 1.098× with the fold. Switching to the fold gave 1.119× with one chain and 1.032× with four. The direct combined gain was 1.231× in this panel.

Run `sh replay.sh width` for four, eight, sixteen and thirty-two chains (arms 0 through 3), each using the fold. In width.csv and width-rebuild.csv, sixteen chains beat four by 1.0273× and 1.0272× in paired median wall time for complete public basis preparation. Median paired CPU gains were 1.0268× and 1.0267×. Each panel uses the same balanced orders and ordered output check as the phase comparison. The general lane-recovery proof in Stripe.lean covers each width.

## Direct comparison with the original setup

Run `sh replay.sh anchor` for the original affine walk, reciprocal completion,
fiber checks and lift-before-trial-division path against the packed sixteen-chain
path with independent smoothness masks. Both regenerate the depth-15 basis on
every call, use the native ordinate lift, and compare every ordered point with
the independent frozen reference. Library loading and process startup precede
measurement. The two CSV files each contain 32 alternating pairs on an Apple M4
Pro with Apple Clang 21.0.0, using a fresh build per panel.

| Panel | Median wall ms, anchor / sixteen | Paired wall speedup | Paired CPU speedup |
| --- | --- | --- | --- |
| anchor16.csv | 54.129 / 1.049 | 51.792× | 51.913× |
| anchor16-rebuild.csv | 54.145 / 0.997 | 54.968× | 54.976× |

Order affected the magnitude. In the first panel the paired median wall
speedups were 48.98× when the anchor ran first and 57.66× when it ran
second. The rebuilt panel gave 49.71× and 58.80× respectively. These
direct measurements cover the full public basis setup and include changes
made before striping was introduced.
