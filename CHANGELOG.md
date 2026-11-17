# Changelog

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
