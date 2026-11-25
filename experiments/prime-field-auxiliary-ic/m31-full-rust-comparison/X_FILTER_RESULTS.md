# Exact x-index rejection: negative full-collector result

The protocol in `X_FILTER_PROTOCOL.md` was frozen before the first timing panel. Both Rust arms used the same sign-packed index, one-multiply slot hash, validated paired-x batch arithmetic, direct pair rows, deterministic relation walk, and modular elimination. The candidate computed each chord x and probed the exact 6 MiB index before materializing y. Both complete sorted index dumps were byte-identical: SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` for auxiliary and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` for plain. All 48 matched pairs agreed on basis digest, verified scalar, trial count, relation count, and table size. The differential Rust test covers ordinary and exceptional additions on B7 and B31. `XFilter.lean` proves that rejecting a candidate only when its x is absent from the exact index preserves the first successful payload lookup, given that exact-index premise.

| Basis | Paired control wall median | X-filter wall median | Median paired control/candidate wall ratio | Candidate wins | Median paired CPU ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 193.6 ms | 264.8 ms | 0.7194 | 2/24 | 0.7444 |
| Plain | 173.0 ms | 235.3 ms | 0.7731 | 2/24 | 0.7772 |

The exact index probe costs more than the skipped ordinate arithmetic in this implementation. The second panel specified in the protocol was conditional on both bases favoring the candidate and therefore was not run. These are local producer measurements on the frozen public fixtures; they do not support a performance gain. Full observations are in `x-filter-raw.csv`.
