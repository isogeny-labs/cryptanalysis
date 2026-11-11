# Chained transfer differential reference

This development oracle compares the native fixed F101 transfer fixture in
[crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877) with the
pre-existing `suite/src/prime_hyperelliptic` BigUint implementation, which is
imported without modification. Both use Cantor arithmetic; these producer-run
checks are not signed independent validation. [pcc:unverified]

## Exact input and source pin

Source E:y²=x³+1, C:y²=x⁶+1, W=(10,0), P=(4,41), r=17 over F101.
The Richelot target is C₂:w²=41z⁶+9z⁴+9z²+41. The upstream native
package is pinned to crypto commit
`b280efc5c22b77718063514c09083af27d6b78c0`; `source-pin.json` and both
SHA-256 manifests bind the exact new and reference sources. The reference
comes from cryptanalysis `68594c8874c75a0a6c04a3874adb1374088ca4f5`.
The initial upstream18db046 pin is retained in `source-pins/` and Git history;
its earlier receipts remain unchanged.

The reference needs a monic quintic. On each odd chart Y²=F(t), let
L=leading(F), a=1/L, t=a*z, Y=a²*Z. Then F(a*z)/a⁴ is monic;
u becomes monic(u(a*z)), v becomes v(a*z)/a². This is an F101 coordinate
change, not an unrecorded twist or a square-root assumption. [pcc:unverified]

## Retained development outcomes

- 10,404 canonical source additions and inverses compared after this change.
- All 289 additions in the Richelot order-17 target subgroup compared.
- All 10,404 rational Richelot source images admitted and compared against a
  fixed-translation addition in the pre-existing target arithmetic.
- Both Jacobian orders recomputed as 10,404 from Fp/Fp² point counts using
  the pre-existing implementation.
- Successor C_s:y²=x⁶+6x⁴+9x²−16 and
  C_t:w²=20z⁶+81z⁴+83z²+21, based at1 and2: both complete9,216-class
  sets have paired additions and both dual norms compared with BigUint;
  independent Fp/Fp² point counts give order9,216, and reference negation
  counts self-inverse classes as4 and16.
- Latest guarded suite receipt: 27 passing tests, one pre-existing benchmark left
  ignored. These are local correctness counts, not performance measurements.
  [pcc:unverified]

Evidence: `evidence/differential-01.txt` through `differential-04.txt`.
Successor receipts: `evidence/successor-development-01.txt` and
`evidence/successor-pinned-01.txt`; the latter completes source guards,
formatting, strict Clippy and full replay against the published b280efc pin.
Records PCC-20261111-5e39d6 and PCC-20261111-820d6f remain unverified until actual signed standing
changes. Strict Clippy's first attempt found the reference's pre-existing
`Fp2Ctx::from_fp(&self)` convention warning. The compatibility annotation is
confined to the imported reference module; no correctness test or reference
arithmetic was changed. Both the warning and subsequent pass are retained.
[pcc:unverified]

## Reproduce

Clone/check out `crypto` and `cryptanalysis` as siblings. In `crypto`, make
the pinned upstream commit available and check out its native source paths;
the rest of the checkout may differ. With Rust/Cargo on PATH, from
`cryptanalysis` run:

```sh
experiments/chained-transfer-reference/check.sh
```

`check.sh` refuses source/reference digest drift before building. The sibling
path in Cargo.toml is deliberate: this avoids a second whole-repository Cargo
Git dependency clone while retaining exact source custody. Cargo.lock freezes
the three small external numeric/build dependencies. CI checks out the two
repositories in the same layout and runs this command.

No standalone DLP solver, experiment allocation, measured speedup, field-family
generalization or full Picard/Richelot formalization is claimed. See the
upstream [report](https://github.com/isogeny-labs/crypto/blob/b280efc5c22b77718063514c09083af27d6b78c0/research/chained_jacobian_transfers_20261110/REPORT_20261111.md)
for the genuine Jacobian hops, duals, zero controls and retained equivalences:
the initial target is isomorphic to its source; the successor has different
rational2-torsion cardinalities and therefore nonisomorphic F101 Jacobians.
Both complete elliptic endpoint functions equal direct elliptic shortcuts.
The preserved prime subgroups are17 and3 respectively, with no extrapolation
to growing fields or an advantage over existing ECDLP algorithms.
[pcc:unverified]

Primary sources reviewed: Galbraith corrected book ch.8 §8.3 and ch.10
§§10.3–10.4; Kunzweiler DCC 2024, DOI 10.1007/s10623-024-01366-1,
§§3.1–3.2. Source review, hashes and unavailable KB/vault notes are in the
upstream `SOURCES_20261111.md`. Canonical transfer/leaderboard graphs are
unchanged because this is unsigned fixed-fixture development evidence.
