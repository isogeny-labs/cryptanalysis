# Changelog

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
