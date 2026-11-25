# Transfer of short bit windows on the public M31 panel

From the repository root, reproduce the exhaustive panel check with PARI/GP and Python 3.10 or later.

```sh
d=experiments/prime-field-auxiliary-ic
gp -q -f "$d/m31-projection-controls/sample.gp" | python3 "$d/m31-four-coverage/window_cover.py"
```

The deterministic sampler retains auxiliary fibers with exactly 17 target-curve lifts among 32 candidate coordinates. The checker verifies all lift labels from the curve equation and checks that all 256 key sets are distinct. The sampled JSON lines had SHA-256 `1f378d051d8d8811bf52b4ed18efd65feb87738bb24bfe4562c60c86e6c78df3`.

The fixed window starting at bit 10 with width 6 separated 27 of the 256 sets. Allowing each set to select any contiguous window, the smallest collision-free width was five for 33 sets, six for 185 sets and seven for 38 sets. A full-coordinate comparison after indexing is required for exact membership.

For seven-bit windows the script computes the greatest attainable coverage for each number of allowed offsets. For one through ten offsets, respectively, the maxima were 91, 154, 198, 224, 237, 248, 251, 254, 255 and 256 sets. One covering family uses zero-based starting positions 0, 1, 3, 4, 9, 12, 15, 17, 19 and 21. All smaller families were exhausted. Each table still selects a suitable single offset for its own keys.

The family was selected on this panel. Counts describe these 256 sets. They do not estimate construction time, query throughput, or coverage on unseen fibers.
