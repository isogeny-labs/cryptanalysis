# PR #1327: retrospective benchmark index

The failed records job identified `benchmarks/20261030-rho-plain-negmap` as an entry without a `bench.record/v1` record. This maintenance adds a new, currently dated retrospective record indexing the existing October 30 study; no experiment was launched and no frozen source, report, protocol or raw data was rewritten. [pcc:unverified]

The original PDF and two compressed row files were recovered from Git commit `a4d8111fc7ac2629ba0d4f4663a249ee68da5d76`; their bytes and SHA-256 hashes match the current artifact manifest. The record quotes the existing `results.json` exactly. It gives only the original shared four-vCPU host description, leaves unknown host/branch/dirty-state/timing/exit metadata null, and labels report commands as documentary templates. Its creation date is the import date, not a backdated execution receipt. [pcc:unverified]

Only the quoted pooled candidate/main ratio enters the generated metric series. Per-size values, intervals and group-ops-only normalizations remain in explicit provenance fields; partial counts are not inserted into the fully priced S headline. No matched-rho number, current-host attribution, S3 upload assertion or signed scientific standing is invented. [pcc:unverified]

`tools/benchrec.py gate` and `check --base origin/main` pass locally across ten records. These checks validate the index and generated report, not the measurements. S3 existence must still pass in credentialed CI. All four generated PDF pages were visually inspected: the existing dense ratio legend remains crowded near the following panel; the shared renderer was not changed in this metadata repair. All existing nine closed records remain byte-identical. [pcc:unverified]
