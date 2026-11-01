# Pinned crypto analysis core

This crate copies the small analysis surface from the private `crypto`
repository at commit `e4f200cc2da058492a9a27f348fb88dc23f8a745`.
`src/avalanche.rs` and `src/statistical.rs` are byte-identical to that
revision; `src/lib.rs` changes only the module paths to these local files.
Run `tools/bootstrap_crypto_analysis_core.sh` from the repository root to
verify the two upstream source hashes before building. This snapshot keeps
local and CI builds independent of cross-repository credentials.
