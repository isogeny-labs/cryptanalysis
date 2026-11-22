# Third-party notices

This repository is licensed under the MIT licence in [LICENSE](LICENSE),
except for the third-party code, patches and documents listed here, which
keep their own licences. The list was made on 2026-11-22 against `main` at
`e89b9db` from the tracked tree, the files' own provenance notes, and each
upstream's licence file, fetched from the URL given. It is a working
inventory for the owners and counsel, not legal advice.
[SECURITY.md](SECURITY.md) has the disclosure and acceptable-use policy.

## Summary

- **GPL code is kept out of the MIT build.** No GPL-licensed source is
  compiled into or linked with the C library (`src/`, `include/`), the Rust
  crates (`suite/`, `crates/`, `bindings/`, `tools/`) or their binaries. The
  GPL components (SageMath, M4GB, WDSat) are patched and built separately
  from their own sources and either run as separate processes or loaded by
  Sage, never linked into this repository's code.
- **Patches to GPL code are GPL.** The SageMath, M4GB and WDSat patches
  stored here are derivative works of their upstreams and are distributed
  under the upstream licence, not MIT.
- **Rust dependencies are not vendored.** `suite/deny.toml` restricts the
  suite's crates.io graph to MIT, Apache-2.0, Unicode-3.0, BSD-2-Clause,
  BSD-3-Clause, CC0-1.0 and Unlicense (`cargo deny --manifest-path
  suite/Cargo.toml check`). The other Rust workspaces have no such check.

## Third-party code, patches and documents stored here

| Path | Upstream | Upstream licence (checked at) | What is here | Obligations and separation |
|:--|:--|:--|:--|:--|
| `experiments/sage-binary-batch/` | [SageMath](https://github.com/sagemath/sage) at `671dfa344f4cc4a6d54f343cbfd1272ee81698c9` (10.10.rc0) | The distribution is GPL-3.0; original Sage library code is GPL-2.0-or-later (`license = "GPL-2.0-or-later"` in its `pyproject.toml`); documentation is CC BY-SA 3.0. [COPYING.txt at the pinned commit](https://github.com/sagemath/sage/blob/671dfa344f4cc4a6d54f343cbfd1272ee81698c9/COPYING.txt), [pyproject.toml](https://github.com/sagemath/sage/blob/671dfa344f4cc4a6d54f343cbfd1272ee81698c9/pyproject.toml) | `sage-binary-batch.patch`; the two new modules in `source/`, which carry `SPDX-License-Identifier: GPL-2.0-or-later`; two unmodified upstream fixture files in `upstream-base/` (a `meson.build` and a reference `index.rst`); Sage's `COPYING.txt`, byte-identical to the pinned commit | GPL-2.0-or-later for the patch and modules; CC BY-SA 3.0 for the documentation fixture. Applied to a separate Sage checkout (`scripts/sage_release.py`), never built into this repository's library or crates |
| `experiments/sage-binary-hardware/`, `sage-binary-native-addition/`, `sage-binary-native-frobenius/`, `sage-binary-point-construction/`, `sage-binary-storage/`, `sage-ic-campaign/*/` (17 further `*.patch` files) | SageMath, same pinned commit | As above | Patches to Sage; `scripts/sage-release-manifest.json` orders eleven Sage patches, the batch patch first, into the released stack | GPL-2.0-or-later, as patches to Sage. See "Release assets" below |
| `third_party/m4gb-patches/` | [M4GB](https://github.com/cr-marcstevens/m4gb) at `01860a52dacb111d6e1533bc7547b2dc8f034073` (`scripts/m4gb_build.sh`) | GPL-3.0: [LICENSE.txt at the pinned commit](https://github.com/cr-marcstevens/m4gb/blob/01860a52dacb111d6e1533bc7547b2dc8f034073/LICENSE.txt) | Four patches and a README that states their GPL-3.0 terms | GPL-3.0. `scripts/m4gb_build.sh` builds M4GB as a separate binary; `ca m4gb` (`tools/ca_cli.c`) only runs it as a child process. No M4GB source is linked |
| `experiments/compact-s3-m4-20261003/q1444_wdsat_adapter/wdsat_adapter.patch` | [WDSat](https://github.com/mtrimoska/WDSat) at `61c6ff3f49445af2729274819edb27b85a89efc1` (the directory's `protocol.json`) | GPL-3.0: [LICENSE at the pinned commit](https://github.com/mtrimoska/WDSat/blob/61c6ff3f49445af2729274819edb27b85a89efc1/LICENSE) | One patch to WDSat, plus the lab's own build and run scripts | GPL-3.0 for the patch. WDSat is built separately and run as an external binary (`--wdsat-binary PATH` in `ca-ic`); not linked |
| `suite/src/cryptanalysis/mq_monica.rs`, `mq_fes.rs` | [ALMASTY MQ](https://gitlab.lip6.fr/almasty/mq) (`monica.c`, `moebius.c`, `ffs.h`); ideas from [libfes-lite](https://github.com/cbouilla/libfes-lite) | Public domain (Unlicense text): [ALMASTY MQ LICENSE](https://gitlab.lip6.fr/almasty/mq/-/blob/master/LICENSE), [libfes-lite LICENSE](https://github.com/cbouilla/libfes-lite/blob/master/LICENSE) | A Rust port of `monica.c`; `mq_fes.rs` reimplements the ideas | None; credited in the module docs |
| `experiments/hashed-ecdl-tensor-reference/reference/quantitative-*.tex` | [openai/math](https://github.com/openai/math), files listed in `reference/SOURCES.json` | Apache-2.0: [LICENSE](https://github.com/openai/math/blob/main/LICENSE); no `NOTICE` file upstream | Two reference TeX snapshots; `reference/LICENSE` is the upstream text | Keep `reference/LICENSE` with the files. `SOURCES.json` notes trailing newlines may be normalised, which Apache-2.0 §4(b) would count as a modification to be stated; it is |
| `verification/pqc-assay/` | [PQC-Assay](https://github.com/amarshat/pqc-assay/tree/6b0096f4a2bda9cf07c7347094affc85d9eb24ff) at `6b0096f4…` | MIT: [LICENSE at the pinned commit](https://github.com/amarshat/pqc-assay/blob/6b0096f4a2bda9cf07c7347094affc85d9eb24ff/LICENSE) | The implementation/model/mathematics split and mutation controls are adopted; `UPSTREAM-LICENSE` is byte-identical to upstream's | Keep `UPSTREAM-LICENSE`. Upstream's copyright line is the template placeholder `<YOUR NAME>` (see open questions) |
| `suite/src/cryptanalysis/md5_hashclash_ffi.rs` | [HashClash](https://github.com/cr-marcstevens/hashclash) | MIT, copyright 2024 Marc Stevens, CWI: [LICENSE.txt](https://github.com/cr-marcstevens/hashclash/blob/master/LICENSE.txt) | `extern "C"` declarations for a `cpc_*` ABI that upstream does not have, and a safe wrapper. No HashClash code | Nothing is linked: the `build.rs` hook the module describes is not in `suite/build.rs`, so every build compiles the `NotLinked` fallback. If it is ever wired up, ship HashClash's MIT notice with the binary |
| `suite/src/cryptanalysis/semaev_corpus.rs` | [EC-Index-Calculus-Benchmarks](https://github.com/mtrimoska/EC-Index-Calculus-Benchmarks) | GPL-3.0: [LICENSE](https://github.com/mtrimoska/EC-Index-Calculus-Benchmarks/blob/master/LICENSE) | Only instance parameters (field, target x-coordinate, planted decomposition); the generated DIMACS/ANF files are deliberately not copied (module docs) | None expected for parameters; see open questions |

## Code from other Isogeny Labs repositories

These are the lab's own code, copied from repositories that are not (yet)
under the same licence. They are offered here under MIT.

| Path | Source |
|:--|:--|
| `suite/vendor/crypto-analysis-core/` | `crypto` at `e4f200cc2da058492a9a27f348fb88dc23f8a745`, hash-pinned (`UPSTREAM.sha256`) |
| `ecc2k130/include/` (device code) | `crypto` `ecc2k130/` at `b8ed2f5` (`ecc2k130/README.md`) |
| `usecases/ecc2k130-gpu/patches/`, `ecc2k130-20b.bundle` | Patches against `crypto` at `c6d2a10` |
| `bindings/rust/curve-audit/catalog/*.json` | `crypto` at `2f1f9c553b4b2f03643f4200d6e12ab9221900c4` (`catalog/PROVENANCE.md`) |
| `crates/hashed-ecdl-tensor/LICENSE`, `bindings/rust/hashed-ecdl-tensor/LICENSE` | MIT, "The cryptanalysis contributors", like the root `LICENSE` |

## External tools run as separate processes

None of these is stored or redistributed here; each is obtained and
built or installed by the user.

| Tool | Licence | How it is used |
|:--|:--|:--|
| SageMath | GPL (above) | Experiments run under a separately built Sage |
| M4GB, WDSat | GPL-3.0 (above) | Separate binaries, run as child processes |
| [M5GB](https://github.com/manschga/M5GB) at `2d063f748e8a16ac5a1d74641c79725df29f67ac` | **None declared** (no licence file or header at that commit or on the repository page, checked 2026-11-22) | `groebner_compare/build_m5gb.py` and the `groebner-comparison` workflow build a bridge from separately cloned upstream source; nothing is vendored |
| [CryptoMiniSat](https://github.com/msoos/cryptominisat) | MIT for everything needed to build and link ([LICENSE.txt](https://github.com/msoos/cryptominisat/blob/master/LICENSE.txt)) | `cryptominisat5` binary (examples) and the optional Python `pysat` binding ([MIT](https://github.com/pysathq/pysat/blob/master/LICENSE.txt)) |
| PARI/GP, Magma | GPL-2.0-or-later ([pari.math.u-bordeaux.fr](https://pari.math.u-bordeaux.fr/)); proprietary (user's own licence) | Optional checkers run by tests and research scripts |
| NVIDIA CUDA toolkit | NVIDIA CUDA EULA | `libcuda` and NVRTC are opened at run time; release builds link the CUDA runtime statically (`ecc2k130/scripts/package.sh`) |

`third_party/cryptominisat-rs-patches/` is in the `crypto` repository, not
here; nothing in this tree uses it.

## Release assets

`.github/workflows/ec2k-gpu-release.yml` publishes, on a release tag:

- Linux CLI and ECC2K-130 CUDA tarballs, which carry this repository's
  `LICENSE` and statically link the NVIDIA CUDA runtime;
- `cryptanalysis-sage-VERSION-source.tar.gz`, the Sage patch stack with its
  manifest and build script (GPL-2.0-or-later material);
- a compiled macOS arm64 overlay of the patched Sage modules (GPL-2.0-or-later
  object code linked against NTL).

## Open questions for the owners

1. **GPL notices in the Sage release assets.** `scripts/sage_release.py`
   adds no licence file to the source kit or the compiled overlay. Distributing
   the overlay's object code needs the GPL text and the corresponding source
   (the source kit plus the pinned Sage commit) offered with it. Add Sage's
   `COPYING.txt` to both archives, or stop publishing the overlay.
2. **The root `LICENSE` has no carve-out.** It says MIT for the whole
   repository; this file is what records the GPL and Apache-2.0 exceptions.
   Consider a sentence in `LICENSE` or the README pointing here.
3. **The copyright holder.** The root `LICENSE` names "The cryptanalysis
   contributors", which was kept unchanged. Decide whether it should name
   Isogeny Labs once the IP assignment (action F1) is signed.
4. **Code imported from `crypto`.** `crypto` has no licence file yet. The
   imports above are offered here under MIT by the same owners; the IP
   assignment and crypto's own licence decision (action F3) should confirm
   that.
5. **M5GB has no licence.** Building it for internal comparison is the
   owners' call; redistributing it or a binary built from it is not permitted
   without the author's permission. M5GB describes itself as a hybrid of M4GB
   (GPL-3.0); whether it derives from M4GB's code is unclear.
6. **PQC-Assay's copyright line** is the placeholder `<YOUR NAME>`. The MIT
   terms are met by keeping the notice, but the holder is unnamed.
7. **EC-Index-Calculus-Benchmarks parameters.** Only instance parameters are
   copied from a GPL-3.0 repository. These are likely facts rather than
   expression; counsel can confirm.
8. **CUDA runtime.** Release tarballs link the CUDA runtime statically;
   confirm it is on the CUDA EULA's redistributable list and whether a notice
   must ship with it.
9. **cargo-deny coverage.** Only `suite/` is checked. `bindings/rust/`,
   `crates/` and `tools/` resolve their own dependency graphs without a
   licence check.
