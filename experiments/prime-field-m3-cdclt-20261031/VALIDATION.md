# Validation receipt

This receipt covers the hardened design and native development fixture. It is
not an experiment export and contains no held-out solver measurement.

## Starting identity

- Repository: `isogeny-labs/cryptanalysis`
- Base commit: `552a13eaca5b28dfc5dc89d5fe3373f8ea40e251`
- Branch: `codex/prime-ic-protocol-hardening-20261101`
- Prior execution-design merge: `8a93e468d6270706622d9cfd08c3a878fa6baf96`

## Native fixture command and observed output

```sh
make -C experiments/prime-field-m3-cdclt-20261031 check
```

Observed with GCC 14.2.0, `-O2 -std=c++20 -Wall -Wextra -Wpedantic -Werror`:

```text
PASS development oracle
fixture p=7 a=0 b=3 order=13
windows=3,2,2 fp2_candidates=96 projected_models=5
checks=sinz_exactly_one,compact_range,lambda_discriminant,t0_branch,disjoint_windows,sign_replay,three_summand_rationality,chained_s3,two_window_oracle
```

The same command also runs the sizing mode. Selected exact rows are:

| s | selectors | Sinz auxiliaries | total Boolean variables | exactly-one clauses |
| ---: | ---: | ---: | ---: | ---: |
| 13 | 24,576 | 24,573 | 49,149 | 73,719 |
| 14 | 49,152 | 49,149 | 98,301 | 147,447 |
| 27 | 402,653,184 | 402,653,181 | 805,306,365 | 1,207,959,543 |

These are structural counts from the selected encoding, not measured solver
memory or time.

The same source was rebuilt with GCC address and undefined-behavior
sanitizers and completed both modes:

```sh
make -C experiments/prime-field-m3-cdclt-20261031 check-sanitize
```

The command exited 0 with the same self-test summary and no sanitizer report.

## Source checks

```sh
sha256sum experiments/compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp
```

Expected and observed digest:

```text
0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6
```

Official cvc5 source was inspected at Git head
`02f77af402b4be82f27e5cc00b86b265a90dea3d`; its finite-field
`TheoryFiniteFields::getProofChecker()` returns `nullptr`. This is a source
capability observation, not a claim about every future cvc5 release.

## Static, report and repository checks

The following checks exited 0:

```sh
make -C experiments/prime-field-m3-cdclt-20261031 check
make -C experiments/prime-field-m3-cdclt-20261031 check-sanitize
git diff --check
test "$(sha256sum experiments/compact-s3-m4-20261003/q1421_work_counted/theory_solver.cpp | cut -d' ' -f1)" = \
  0a0d2c673e9484f4b217917ee306e7663140e4d4618d8bb0ed8dc91947d08bc6
rg -q 'a < 1.5' experiments/prime-field-m3-cdclt-20261031/PROTOCOL.md
rg -q 'every preregistered natural row' experiments/prime-field-m3-cdclt-20261031/PROTOCOL.md
rg -q '805,306,365' experiments/prime-field-m3-cdclt-20261031/PROTOCOL.md
rg -q 'no finite-field proof checker' experiments/prime-field-m3-cdclt-20261031/PROTOCOL.md
dot -Tsvg experiments/prime-field-m3-cdclt-20261031/hardening-flow.dot \
  -o experiments/prime-field-m3-cdclt-20261031/hardening-flow.svg
pandoc experiments/prime-field-m3-cdclt-20261031/HARDENING_REPORT.md \
  --pdf-engine=xelatex \
  -o experiments/prime-field-m3-cdclt-20261031/HARDENING_REPORT.pdf
pdftotext experiments/prime-field-m3-cdclt-20261031/HARDENING_REPORT.pdf -
```

The report is a two-page, text-extractable PDF. Its diagram was also visually
inspected after rendering.

The broad repository command `make test JOBS=2` was attempted and stopped
before configuration with exit 2 because `cmake` is not installed in this
environment (`make: cmake: No such file or directory`). No broad C-library
test executable ran; CI remains the independent repository-wide gate.

## Evidence boundary

- Scientific rows created: 0
- Held-out instances generated: 0
- External solver runs: 0
- Timings or performance conclusions: 0
- Implemented scope: deterministic small-field semantic oracle, mutation
  controls, exactly-one semantics and representation sizing
- Still missing: production IR, `F_p` external propagator, explanation/proof
  checker, exporters, counted instrumentation, analysis/power source and
  resource preflight
