# Changelog

## [0.1.17](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.16...cryptanalysis-v0.1.17) (2026-11-23)


### Features

* **research:** compose CT315 cost and CT317 group replay on same raw panel ([a740f85](https://github.com/isogeny-labs/cryptanalysis/commit/a740f8560cd6c34fcb759bc1c02fc8390e8c89a2))


### Bug Fixes

* **ct319:** bind every cold wall/RSS and invocation to CT304 capture bytes ([284c8c5](https://github.com/isogeny-labs/cryptanalysis/commit/284c8c5addbd86a5f134a761b0a447bb4d57064e))
* **ct321:** match existing CT318 synthetic source curve identity ([c088ec9](https://github.com/isogeny-labs/cryptanalysis/commit/c088ec986b7c3240b7ae6ef3fcc70a9fa465cf4a))
* **ct321:** preserve random-range callback signature in publish fixture ([049e84c](https://github.com/isogeny-labs/cryptanalysis/commit/049e84ce60bd7aea6263e4d4030cc9856afffa87))
* **ct324:** derive Hash for canonical distinguished-point table keys ([57d04c0](https://github.com/isogeny-labs/cryptanalysis/commit/57d04c03017a070092cba48874cea27f47f3fad2))
* **ct324:** omit private post-reveal scalars from public cold-panel evidence ([adec294](https://github.com/isogeny-labs/cryptanalysis/commit/adec2949a8c8de82118ac0a77327ef54a41cd7b4))

## [0.1.16](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.15...cryptanalysis-v0.1.16) (2026-11-22)


### Features

* **prime-orbit-ic:** Aut-equivariant signed multi-orbit box (wsum) collector on Generic/J1728/J0 ([851f544](https://github.com/isogeny-labs/cryptanalysis/commit/851f54459eb2268f697881c5f24a2763652ac14f))

## [0.1.15](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.14...cryptanalysis-v0.1.15) (2026-11-22)


### Performance

* document R7 measured regression and unresolved native gate ([0860c0f](https://github.com/isogeny-labs/cryptanalysis/commit/0860c0f10aa3c3a3ccc95ee3e2fe8857e3c98c0d))
* document rejected short-row SpMV specialization (no kernel change) ([3eedc70](https://github.com/isogeny-labs/cryptanalysis/commit/3eedc70b433a1f86501a3cd7fb58e9c1018a6fe7))
* document rejected Shoup branchless reduction R5 with frozen profile and paired null results ([fe23256](https://github.com/isogeny-labs/cryptanalysis/commit/fe23256a3fc2f5d78df1eb5d5ded7d4e78a10876))
* preregister R7 aligned coefficient-cursor diagnostic ([a057a38](https://github.com/isogeny-labs/cryptanalysis/commit/a057a38425e59443d5838dd44d8e0069d612c738))
* preserve all 60 paired timing records for Shoup R5 null result ([848b83c](https://github.com/isogeny-labs/cryptanalysis/commit/848b83cbac90b2002141df107719e17c3831f97c))
* preserve all 60 R7 paired CPU and wall ratios ([3466cd8](https://github.com/isogeny-labs/cryptanalysis/commit/3466cd88b621c8b7ce2b847b26764c326f1069c0))
* record R6 rejected two-chain light-row nonunit diagnostic ([d97ae7a](https://github.com/isogeny-labs/cryptanalysis/commit/d97ae7a0908aecc715869c59da147b01034d67c7))
* record rejected four-chain sparse Lanczos gather (no source change) ([731fe58](https://github.com/isogeny-labs/cryptanalysis/commit/731fe58dc08e85d975f7e059ebdbf4dc83a0e8b7))
* reject aligned light-row coefficient cursor (R7 paired diagnostic) ([ec83940](https://github.com/isogeny-labs/cryptanalysis/commit/ec83940a0163eb7f8bfa329e721a5cd960409b12))
* reject hoisted-bound sparse Lanczos gather (120-run diagnostic) ([efb1fc7](https://github.com/isogeny-labs/cryptanalysis/commit/efb1fc795252b88536d75650a8fa3220f4c4539e))
* reject Shoup branchless correction (R5 120-run null) ([82e6d03](https://github.com/isogeny-labs/cryptanalysis/commit/82e6d030ce946deeaec56592d14eec0fae3d138e))
* reject two-chain light-row nonunit accumulator (R6 paired profiling) ([3e79364](https://github.com/isogeny-labs/cryptanalysis/commit/3e7936483e2956dd9902462420be182f1383676b))
* reject two-term light-row nonunit unroll (R8 paired diagnostic) ([3779998](https://github.com/isogeny-labs/cryptanalysis/commit/37799986fe7476ec11bae5ed38d6bbbf5fdc5685))
* retain all R6 paired CPU and whole-process timing samples ([3c997e9](https://github.com/isogeny-labs/cryptanalysis/commit/3c997e9f4d3986b31b41372a2c399455c1858791))
* Round 1–3 ECDLP/IC/isogeny/field arithmetic speedups ([e5b41e3](https://github.com/isogeny-labs/cryptanalysis/commit/e5b41e32788097a36fca4ddaf437bdfa9e758323))
* Round 10 FastCurve BigUint bridges for CM/graph ([1b81e3f](https://github.com/isogeny-labs/cryptanalysis/commit/1b81e3f707906a8d51075409dfb2ed1d994dddaf))
* Round 11 FastCurve Pollard rho for isogeny attack ([992d1b4](https://github.com/isogeny-labs/cryptanalysis/commit/992d1b47349a819feca3edef67f0652358a2459b))
* Round 12 FastCurve multi-target GLS rho ([d2c25e9](https://github.com/isogeny-labs/cryptanalysis/commit/d2c25e9d996ee3dd9f31053869fc0c2f60caed80))
* Round 14 Jacobi Legendre, Tonelli mont, Zp op fast path ([1b8b086](https://github.com/isogeny-labs/cryptanalysis/commit/1b8b086a04b6090e028fecbcdff044faff95f4c4))
* Round 15 lazy Montgomery REDC for Zp chains ([19d3687](https://github.com/isogeny-labs/cryptanalysis/commit/19d3687b676adde9d57e07ce47e7f9d3d3a5e69c))
* Round 16 dual interleaved Pollard-Brent factorize ([e0440b4](https://github.com/isogeny-labs/cryptanalysis/commit/e0440b4bd2ef443322d47100677195f3d4e98541))
* Round 17 sliding-window w=4 EC scalar mul ([ea4f4c2](https://github.com/isogeny-labs/cryptanalysis/commit/ea4f4c2efd88de1e813667094ac1fe5fcb65319f))
* Round 18 lazy REDC Montgomery pow ladder ([0a84bfa](https://github.com/isogeny-labs/cryptanalysis/commit/0a84bfa29c5ee78078f0d9cbd1f98f68a6b603a9))
* Round 19 lazy REDC Jacobian EC arithmetic ([a8744ac](https://github.com/isogeny-labs/cryptanalysis/commit/a8744ac75b2830a4ee2015825ac1d1d6d052f253))
* Round 20 fused Kaliski Montgomery inverse ([8db9bc6](https://github.com/isogeny-labs/cryptanalysis/commit/8db9bc6fc13873c6321ada9adae1d6629d5d4d13))
* Round 21 fused native-EC kangaroo hops ([1a3bc25](https://github.com/isogeny-labs/cryptanalysis/commit/1a3bc25829a46e8375c7fcaae3490bf43725e737))
* Round 22 shared-addend Mestre BSGS ([66258de](https://github.com/isogeny-labs/cryptanalysis/commit/66258def039120cf36598b73901fc4fa67c9adcd))
* Round 25 hashed 7-base Miller–Rabin ([6ae6a83](https://github.com/isogeny-labs/cryptanalysis/commit/6ae6a834c7243f2f8c1d70440f414f537fb6a09d))
* Round 29 SoA affine addend tables for EC rho/kangaroo ([6d82ee5](https://github.com/isogeny-labs/cryptanalysis/commit/6d82ee5d145558d971c1ce486ffa5cdf80b9f8a2))
* Round 36 Cheon orbit lanes 8 ([a9cd4e9](https://github.com/isogeny-labs/cryptanalysis/commit/a9cd4e91a292e0476d995389036d90849342d7de))
* Round 4 Barrett ca_mulmod, kangaroo mod, and test gates ([14d8c2b](https://github.com/isogeny-labs/cryptanalysis/commit/14d8c2b456a2e8939e94f78e5956722fba021d81))
* Round 5 route remaining u128 mods through Barrett ([07852ae](https://github.com/isogeny-labs/cryptanalysis/commit/07852ae4a7d9d2084f6b3e62b976afcb872d087c))
* Round 6 Lemire residues in the linear IC sieve ([150a255](https://github.com/isogeny-labs/cryptanalysis/commit/150a255371d5416591fe3cb168e5a9a4146e1f35))
* Round 7 AArch64 ecc2k 4-lane NEON+PMULL ([099a221](https://github.com/isogeny-labs/cryptanalysis/commit/099a22145513ef0b1da3d1df7c33f2a6cc3b84fd))
* Round 8 IC sieve 32-bit inv and wider trial scans ([0b90fee](https://github.com/isogeny-labs/cryptanalysis/commit/0b90fee3b90358348499861ed7dbc7c2360c4f25))
* Round 9 dual-chain Lanczos vdot and sieve lim filter ([41108c3](https://github.com/isogeny-labs/cryptanalysis/commit/41108c389c46dc9d52e2b97b39d52b3ad72e29b7))
* Rounds 1–12 ECDLP/IC/isogeny/field arithmetic speedups ([80c9f4d](https://github.com/isogeny-labs/cryptanalysis/commit/80c9f4dd9db89fca90bead8083389660448a3a40))

## [0.1.14](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.13...cryptanalysis-v0.1.14) (2026-11-18)


### Features

* add native ECC2K-130 index-calculus preflight ([b7abc1e](https://github.com/isogeny-labs/cryptanalysis/commit/b7abc1edf35daa60d676e24f74c12e5124d01733))


### Bug Fixes

* **ct200:** accept only audited duplicate PCC keep entry in policy drift ([d830a5e](https://github.com/isogeny-labs/cryptanalysis/commit/d830a5ee937143daeee71a6619d416e7b296274d))

## [0.1.13](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.12...cryptanalysis-v0.1.13) (2026-11-18)


### Features

* certify nine-point xedni plane relations ([31c6e60](https://github.com/isogeny-labs/cryptanalysis/commit/31c6e6016c295407c9940b37c7282291ae21e45a))
* **ct192:** bind explicit direction and source group metadata to raw 96-packet records ([87b400a](https://github.com/isogeny-labs/cryptanalysis/commit/87b400adc2b5541e4004c5d825516c13966fd60d))
* **ct192:** exact CT125 source derivative and public-48 guarded admission ([29d4301](https://github.com/isogeny-labs/cryptanalysis/commit/29d430116ad84cce4f43c4f8c7419c96df7ebf6f))
* **ct192:** native-eligible scalar-blind 48-operand N2_actual and D_padd paired panel ([2b4f8c4](https://github.com/isogeny-labs/cryptanalysis/commit/2b4f8c4be64042b2b80d3ecf06c6ace002f9038c))


### Bug Fixes

* **ct190:** pin real CT175 cold-request expression ([28b78f3](https://github.com/isogeny-labs/cryptanalysis/commit/28b78f3b62bb5866d7182c7833cd1e48c5eaebc3))
* **ct192:** audit package identity separately from dependency declarations ([7945795](https://github.com/isogeny-labs/cryptanalysis/commit/7945795be4541121350241e55bf7173e2714ec11))
* **ct192:** correct literal Git blob NUL and source newline escapes ([9a51079](https://github.com/isogeny-labs/cryptanalysis/commit/9a51079551902fbb7f7d6c0336a2f27e8eb3d354))
* **ct192:** emit real module path newlines in materialized Rust ([cfac2b2](https://github.com/isogeny-labs/cryptanalysis/commit/cfac2b213a43cfd1d93c275e186659feba13ba9a))
* **ct192:** use unambiguous Rust CLI admission predicates ([e8bd7de](https://github.com/isogeny-labs/cryptanalysis/commit/e8bd7de6d52eb0edd30ea5b2eab978288a9ae343))
* **ct193:** check target Jacobian class as well as doubled norm in pre-norm probe ([e8ffd96](https://github.com/isogeny-labs/cryptanalysis/commit/e8ffd96063a708e7542f1aa0276a8f6106c45b7d))
* **ct193:** remove mistaken positive mutation duplicating final check ([e7bfdd4](https://github.com/isogeny-labs/cryptanalysis/commit/e7bfdd4a9b08af450046b182e4fb0daac18302df))
* **CT194:** input-opaque operand per timed primitive repetition ([b46fa91](https://github.com/isogeny-labs/cryptanalysis/commit/b46fa915025fb39f2ee2ede63d9b1b8b7ad51860))
* restore suite build after binary subtract merge ([9b75b92](https://github.com/isogeny-labs/cryptanalysis/commit/9b75b92519d575a1e72d6085055baea6053add75))

## [0.1.12](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.11...cryptanalysis-v0.1.12) (2026-11-17)


### Bug Fixes

* **ct187:** prevent plan mode execution flag bypass ([84b51b2](https://github.com/isogeny-labs/cryptanalysis/commit/84b51b22e801ccc5acc0c43fc15abc77330b2b0e))

## [0.1.11](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.10...cryptanalysis-v0.1.11) (2026-11-17)


### Features

* **ct182:** add independent versioned counterbalanced v2 panel adjudication with strict legacy child checks ([8745412](https://github.com/isogeny-labs/cryptanalysis/commit/87454126a73744f75d0c0bc384b3035e55815226))


### Bug Fixes

* **ct178:** require total wall budget and truncate each native child allowance ([d873cfc](https://github.com/isogeny-labs/cryptanalysis/commit/d873cfcf115317427caf870e6b8c0dc7ceca1a64))
* **ct179:** bind recorded child command and match lossless pipe rendering ([317b2a6](https://github.com/isogeny-labs/cryptanalysis/commit/317b2a6961a3c1fca7b8b626346f8ba96046821e))
* **ct180:** encode actual JSONL newline in mutation tests ([2374402](https://github.com/isogeny-labs/cryptanalysis/commit/237440225c06ef1e82dab7a47906b15746da847d))
* **ct180:** reject impossible nested cold-process timing transcripts ([bbf6e83](https://github.com/isogeny-labs/cryptanalysis/commit/bbf6e83e43aaca66e1f6a37f55c614cafb7128cc))
* **ct185:** use defined pinned-reader environment variable ([0d4ce55](https://github.com/isogeny-labs/cryptanalysis/commit/0d4ce551d166358aad6c33a6452ea784dfc4d2dd))

## [0.1.10](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.9...cryptanalysis-v0.1.10) (2026-11-17)


### Features

* **ct175:** measure one native public packet in a fresh process without preflight warmup ([dba326f](https://github.com/isogeny-labs/cryptanalysis/commit/dba326fdd3d0f06d38f55f755cae578a0c3a5dce))


### Bug Fixes

* **ct175:** exclude rustc child-process probe from cold sample wall time ([2b89f4a](https://github.com/isogeny-labs/cryptanalysis/commit/2b89f4a7c2d1613e6896656eb0d727f9bd0e4696))
* **ct176:** pin actual Git blob bytes and preserve raw process failures ([61679d1](https://github.com/isogeny-labs/cryptanalysis/commit/61679d1e1a3f2cafe1bbe32727e0d1086170700b))
* **ct176:** terminal refusal matches incomplete-panel exit status ([4564b89](https://github.com/isogeny-labs/cryptanalysis/commit/4564b8944b0a47a1aa086dcfb812864bac720c5f))

## [0.1.9](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.8...cryptanalysis-v0.1.9) (2026-11-17)


### Features

* **ct172:** add scalar-blind exact native replay for 48 frozen public packets ([c1ca4df](https://github.com/isogeny-labs/cryptanalysis/commit/c1ca4df47acf4695b0e06c67e5871b64bf7f8f72))


### Bug Fixes

* **ct172:** bind CT125 and frozen fixture at correct sibling source root ([d213e40](https://github.com/isogeny-labs/cryptanalysis/commit/d213e409f156c7e729e299c259f1f5bbc592a284))
* **ct172:** correct exact-head Actions ref expression ([eff1dd5](https://github.com/isogeny-labs/cryptanalysis/commit/eff1dd5b6aae9982daffdbbac9fb5d72a13c3e08))
* **ct172:** make CLI gate explicit and type-safe ([b984778](https://github.com/isogeny-labs/cryptanalysis/commit/b9847782f39ff54005c62c51ac2a0fabe84b448b))

## [0.1.8](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.7...cryptanalysis-v0.1.8) (2026-11-17)


### Bug Fixes

* **ct170:** bind all three frozen census partitions, not just point totals ([215ef6e](https://github.com/isogeny-labs/cryptanalysis/commit/215ef6eb5715c8ce42524d31d6c9e3c186a812d4))
* **ct171:** bind source guard to actual frozen fixture Git blob ([8b221fe](https://github.com/isogeny-labs/cryptanalysis/commit/8b221feab72e9210f1ce01a4b556164bfca92887))
* **ct171:** bind source guard to actual frozen fixture Git blob ([13f33d1](https://github.com/isogeny-labs/cryptanalysis/commit/13f33d1856cd99a15a527775faf20a130d171ba2))

## [0.1.7](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.6...cryptanalysis-v0.1.7) (2026-11-16)


### Bug Fixes

* **ct168:** exclude harness-only public Q construction from cold timing ([40568e4](https://github.com/isogeny-labs/cryptanalysis/commit/40568e4d6ef43a26f87ca5431fe357b7bde7ded1))
* **ct168:** fail closed on truncated census, typed values and schema spoofing ([76a8077](https://github.com/isogeny-labs/cryptanalysis/commit/76a80779735476d0a48bc632b6b0fe85b9ceb2e9))
* **ct168:** isolate public-Q timed solvers from known verifier scalar ([c06d255](https://github.com/isogeny-labs/cryptanalysis/commit/c06d2552139400ecb3fb78124aff8c12f390ffe0))
* **ct168:** preserve exact 22-digit integer Frobenius traces in frozen JSON ([69daaa9](https://github.com/isogeny-labs/cryptanalysis/commit/69daaa9c4f8ecfc5f7e559f9b53557e0356630d9))

## [0.1.6](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.5...cryptanalysis-v0.1.6) (2026-11-16)


### Features

* **ic:** native batched binary subtraction and frontier controls ([b96d797](https://github.com/isogeny-labs/cryptanalysis/commit/b96d797fd56019a7fa42e81b4bc9e035b1cd18dd))

## [0.1.5](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.4...cryptanalysis-v0.1.5) (2026-11-16)


### Bug Fixes

* **artifacts:** retain PCC ledger as the Git trust witness ([148d8b6](https://github.com/isogeny-labs/cryptanalysis/commit/148d8b66c6c6b36e15db469c5745085643c5dd0d))
* **artifacts:** sync canonical source and enforce native parity ([f7dfc2a](https://github.com/isogeny-labs/cryptanalysis/commit/f7dfc2a55917a22780052384c33d91829c41196f))
* **ci:** correct log proof classification and projection controls ([d9ee51f](https://github.com/isogeny-labs/cryptanalysis/commit/d9ee51f20644b412a909dffec37c94907e7eba86))
* **ci:** pin PCC trust and ledger checks to the tested merge base ([5dfcf82](https://github.com/isogeny-labs/cryptanalysis/commit/5dfcf82e698db8d895452c7089f566d3e68d1337))
* **ci:** retain claim history and harden projection controls ([a6ee96c](https://github.com/isogeny-labs/cryptanalysis/commit/a6ee96c4b0410097a72fc4405dd21ab7e5aca1db))
* **ct157:** reject boolean/float aliases in 695-record parity [pcc:unverified] ([7a77cf0](https://github.com/isogeny-labs/cryptanalysis/commit/7a77cf046af8a80cbe8f3516260be66575d86233))
* **ct159:** type-preserving native C169/C13/D pricing evidence audit ([8f26796](https://github.com/isogeny-labs/cryptanalysis/commit/8f267962f8d6992c5dda622fd4735a96fcd80b9b))
* **ct159:** typed finite JSON and ABBA public identity price guards ([658dca5](https://github.com/isogeny-labs/cryptanalysis/commit/658dca512276c426d5e04c291193a49717824170))
* **grumpy:** bound automatic floating step conversion ([c539cd1](https://github.com/isogeny-labs/cryptanalysis/commit/c539cd11aed992bf80b501b76296b9751c55485b))
* **grumpy:** validate checkpoint counters before resume and iteration ([443641b](https://github.com/isogeny-labs/cryptanalysis/commit/443641b50c4a33fb128ea2b4319095cf7b46ab4a))

## [0.1.4](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.3...cryptanalysis-v0.1.4) (2026-11-16)


### Bug Fixes

* sync canonical finite benchmark arithmetic and chart bounds ([854d70d](https://github.com/isogeny-labs/cryptanalysis/commit/854d70df60629a011ee587d608c6d02278521ecb))
* validate GPU checkpoint metadata and cumulative counter capacity ([91b7bc0](https://github.com/isogeny-labs/cryptanalysis/commit/91b7bc037911edb27f288498058c2d5cde057b7d))

## [0.1.3](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.2...cryptanalysis-v0.1.3) (2026-11-14)


### Features

* **cli:** ca m4gb runs the external M4GB Gröbner solver ([e082a0e](https://github.com/isogeny-labs/cryptanalysis/commit/e082a0e0008ac1becd1228ceb349d6fb8dde4e8a))
* **cli:** ca m4gb runs the external M4GB Groebner solver ([955f31d](https://github.com/isogeny-labs/cryptanalysis/commit/955f31d60a75de1c24c3ff663b67fd3e3201528e))


### Performance

* WALL-only pass over precomp/BSGS/grumpy, linalg, kangaroo/Cheon/Pohlig/modarith, ec_tau and the Rust suite ([0d69fc5](https://github.com/isogeny-labs/cryptanalysis/commit/0d69fc5526c02c4071db896d8800be74929f4ff7))

## [0.1.2](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.1...cryptanalysis-v0.1.2) (2026-11-07)


### Bug Fixes

* **release:** trust the dimpase tap before installing Sage prerequisites ([e19dc2b](https://github.com/isogeny-labs/cryptanalysis/commit/e19dc2b5081ced0f7cdea916e87bca25c8c9ab64))
* **release:** trust the dimpase tap before installing Sage prerequisites ([4d96b51](https://github.com/isogeny-labs/cryptanalysis/commit/4d96b51e7e1d785dac872dd3592f1a5c81028e36))

## [0.1.1](https://github.com/isogeny-labs/cryptanalysis/compare/cryptanalysis-v0.1.0...cryptanalysis-v0.1.1) (2026-11-07)


### Features

* add exact factoring and weighted profiles to both tensor entry points ([238d5bb](https://github.com/isogeny-labs/cryptanalysis/commit/238d5bb6061429ce464b60b6fcf7637064667fb4))
* **icx:** audit xedni across curve families ([9150563](https://github.com/isogeny-labs/cryptanalysis/commit/91505638351f8b61d9cefdafb51881b28fce3f50))
* integrate native hashed ECDL tensor pipeline ([d6b0adc](https://github.com/isogeny-labs/cryptanalysis/commit/d6b0adc4937158e8077ac6ccf9352f4f4d735769))
* mirror bounded finite-size ECDLP backends and validation ([57e8809](https://github.com/isogeny-labs/cryptanalysis/commit/57e88095b9dc70cf0ecfdb1103bf3e28b6bb0642))


### Bug Fixes

* **ci:** expose native proof compiler failures without discarding raw diagnostics ([58c893d](https://github.com/isogeny-labs/cryptanalysis/commit/58c893d84030ceeb2a85a23aec226eec79e78bf4))
* fit tensor report to store policy and extend recursion controls ([76e7138](https://github.com/isogeny-labs/cryptanalysis/commit/76e7138f455732888bfc2ee86d243052279e6d2a))
* **hecke:** retain interrupted cost measurements and cancel alarms ([2ed698e](https://github.com/isogeny-labs/cryptanalysis/commit/2ed698efcae1e0a84ca1283f6a16c6da8a25fa07))
* **lean:** elaborate zero-tuple witness controls without free-variable or cast simplification errors ([73b455c](https://github.com/isogeny-labs/cryptanalysis/commit/73b455cdbed119c3189fd92fab5ac7f6a897e565))
* pick up the deduplicated usage audit ([a9cdf34](https://github.com/isogeny-labs/cryptanalysis/commit/a9cdf34dd062984e7002606c1b3b03a3d79df331))
* pick up the deduplicated usage audit ([1a102a8](https://github.com/isogeny-labs/cryptanalysis/commit/1a102a81104959f543c2e2fe62850a38b5358ccd))
* preserve caller randomness during tensor certificate replay ([b2908f1](https://github.com/isogeny-labs/cryptanalysis/commit/b2908f13f8cba94b0257551d443fc98d71668efa))
* **proof:** replace circular xedni bound with a witness successor ([adbee08](https://github.com/isogeny-labs/cryptanalysis/commit/adbee087156a61bd2026e3947b9cf95d86ccf9d6))
* reject ambiguous tensor receipts and bound input reads ([9c43bb1](https://github.com/isogeny-labs/cryptanalysis/commit/9c43bb1d8d31d7564e4d640c6bfb6683e72fd2af))


### Performance

* reuse square-root setup for hashed-ECDL enumeration ([b02b919](https://github.com/isogeny-labs/cryptanalysis/commit/b02b919d4eec0691dd00438d0e0d9ca7f26fedce))
