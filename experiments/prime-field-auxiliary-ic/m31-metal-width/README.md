# Batch size for M31 Metal inversion

The panel compiles widths 4, 8, 16 and 32 from the batch8 kernel in ../m31-metal-inverse/inverse.metal. The fifth arm independently creates a second width-8 pipeline. Inputs, arithmetic and the ceiling-stride layout are shared. Stride.lean proves index coverage for a positive stride with sufficient capacity and uniqueness of the lane and slot. The driver checks every output by modular multiplication, including zeros modulo p and an incomplete final batch.

Build with clang++ -O3 -std=c++17 -fobjc-arc -Wall -Wextra -Werror panel.mm -framework Foundation -framework Metal -o panel. Run ./panel 291231 and ./panel 291232 from this directory. Each process warms all arms, rotates input sizes and balances position and order over 30 rounds. Compilation and allocation precede timing. Device time comes from command-buffer timestamps; wall time includes encoding, submission and waiting. Raw CSV contains round, element count, arm index, thread width and both timing intervals.

| Input elements | Lowest median device time width in both panels | Paired device time ratio, width 8 / indicated width |
|---:|---:|---:|
| 8192 | 4 | 1.369, 1.358 |
| 65536 | 4 | 1.084, 1.077 |
| 262147 | 8 (including duplicate) | reference |
| 1048576 | 16 | 1.057, 1.076 |

On the shared M4 Pro, the million-element width-8/16 paired wall ratios were 0.930 and 1.163. The duplicate width-8 paired wall ratios at the same size were 0.925 and 1.272. The device data support a size-dependent width effect. Application-level elapsed time remains unresolved.
