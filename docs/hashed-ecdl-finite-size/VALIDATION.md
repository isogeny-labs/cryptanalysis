# Mirrored implementation validation

The commands and exact 81-test breakdown are in [README.md](README.md).
`tests.txt.gz`, `clippy.txt`, `msrv.txt` and `source-check.txt` are this
integration's raw final receipts. `../hashed-ecdl-finite-size-sources.sha256`
binds the actual binding sources, examples and workspace lock/manifests.
Strict lint, MSRV and formatting pass; remote checks/review remain separate.

The copied PDF/source describes both integrations and the original crypto
receipt at e2c36e34c404907821a1e013d4b4dee49f09a0c3. Later crypto main
refreshes are recorded separately on #2930 rather than rewriting those raw
records. Native shared additions are byte-identical; pre-existing core
hash-prime/pruning/JSON/point/reader differences are retained.

Both PDF pages were rendered and visually inspected. The graph/source/PDF
are unchanged copies. No new performance, scaling, coverage, sub-rho,
challenge-solve or mathematical-proof claim is established. Item3's
smaller-packet proof and the independent audit remain open.
