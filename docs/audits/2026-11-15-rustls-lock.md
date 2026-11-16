# Optional Redis TLS dependency update

At main `66b636486d04018aef499fb1ba92cee414fe1fa4`, `suite/Cargo.lock` selected Rustls 0.23.45 through optional `redis-cache` support. The default suite features are empty; this receipt does not establish use or exposure of a running service.

The four open repository alerts name Rustls and list 0.23.46 as their first patched stable version:

- [ECH rejection and buffered application data](https://github.com/rustls/rustls/security/advisories/GHSA-vp88-798v-h67f)
- [Per-name key-exchange record poisoning](https://github.com/rustls/rustls/security/advisories/GHSA-w44r-93j7-qv28)
- [Session debug formatting and TLS secrets](https://github.com/rustls/rustls/security/advisories/GHSA-c8m5-c952-6cm4)
- [Certificate decompression allocation](https://github.com/rustls/rustls/security/advisories/GHSA-h2v8-394m-p7vv)

Cargo updated only Rustls's version and registry checksum to 0.23.46. No manifest requirement, other dependency entry, source mirror or experiment record changed. `cargo check --locked --features redis-cache --lib` passes using installed Rust 1.99.1. Focused `cryptanalysis::algebra_cache::tests` with that feature enabled passes 10 tests; the existing dedicated Redis-server integration test remains ignored by its source declaration. No live TLS handshake or Redis server test was run, and the declared Rust 1.87 floor was not checked locally. These are producer-reported software controls pending independent review. [pcc:unverified]

Commands used the task-owned target directory, two build jobs, disabled incremental compilation, and debug level zero. The first sparse-checkout attempt lacked the local Rust binding manifest; the first compile then lacked the tracked curve corpus. Both tracked inputs were materialized and the failed logs retained. A local rust-objcopy debug-stripping warning is retained; it did not prevent the subsequent check or tests. Global toolchains and dynamic-library paths are unchanged.
