# Post-review correction: two-sided Chernoff bounds

The first recorded suite was produced at source revision
`8a3ee1d85cbb32b0fb78aa8b92cc363e3e0caffd`. Its `tail_bound` implementation
computed `2 exp(-n D(x || p))` from the observed rate `x`. Bernoulli KL
divergence is asymmetric; for a sparse null and an observation below the null
rate, that expression can understate the opposite upper tail. The archived
`primary_family_bound` and `control_family_bound` fields preserve those original
values and must not be cited as conservative two-sided bounds.

The implementation now adds separate Chernoff bounds at the lower and upper
cutoffs corresponding to the observed absolute deviation. A regression test
compares the result with the exact binomial tail probability for `n=1000`,
`p=0.1`, and 50 hits, where the old shortcut is too small.

[`statistical-recheck.json`](statistical-recheck.json) applies the corrected
bound to the archived hit counts. It does not call AES, draw samples, repeat a
search, or change the original run. The corrected family classifications are
unchanged: two candidates pass every validation key at one round and two at two
rounds; no candidates pass in the other ten families; and all twelve matched
PRP control families remain non-rejected. The original raw archive and rendered
suite reports remain unchanged as historical records; this correction governs
the statistical interpretation and all future validations.

Reproduce the recheck after extracting `runs.tar.xz`:

```sh
cargo run --release --locked --manifest-path tools/aes-discover/Cargo.toml \
  --example recheck_bounds -- \
  experiments/aes-distinguisher-lab-20261017/runs/20261017-first-suite \
  > /tmp/aes-lab-statistical-recheck.json
```

Compare the generated output with `statistical-recheck.json`. Raw file hashes
for all twelve validation reports are recorded there.
