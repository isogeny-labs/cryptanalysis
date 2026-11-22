# Auxiliary independence certificates for the fresh beam panel

**All 104 rational point pairs retained at depth eight by the frozen width-eight beam on the 13 fresh-panel public hits are `Z`-linearly independent on their exact rational curves.** The original, predeclared odd-prime census through 199 certified 100 pairs. A separately frozen adaptive extension over primes 211–997 certified the four remaining pairs. Independent Python finite-group replay passed all 5,168 state-prime rows and every first-witness choice.

For each pair, a good auxiliary reduction with odd group order excludes rational 2-torsion. A possibly different good reduction sends `P1`, `P2`, and `P1−P2` outside the doubled-point image. Their classes are therefore independent in `E(F_ell)/2E(F_ell)`. Any integer relation has both coefficients even; absence of rational 2-torsion permits infinite descent. This conclusion addresses **every** integer coefficient pair for these exact 104 rational lifts. The [known-coefficient construction](../xedni-known-relation-lifts-20261118/README.md) uses different, relation-dependent lifts and is compatible with this result.

## Frozen census and adaptive extension

[`protocol.json`](protocol.json) pins the compressed [fresh-panel result](../xedni-hensel-fresh-transfer-20261118/run-result.json.gz), all eight final beam states for each of its 13 admitted hits, and every odd prime from 3 through 199. It fixes good-model and point-reduction tests, both witness criteria, the 1,200-second cap, and failure retention. The checked Sage run completed **4,680** state-prime rows: 239 bad-model reductions and 4,441 good point reductions. All 104 states obtained an odd-order witness; 100 also obtained a quotient witness. The original [`run-result.json`](run-result.json), [`rows.json.gz`](rows.json.gz), and [`audit-result.json`](audit-result.json) preserve those outcomes, including the four original `uncertified_in_prime_cap` statuses.

After the original result, [`extension-protocol.json`](extension-protocol.json) fixed precisely those four open state IDs, bound the parent result and rows by SHA-256, and selected every prime from 211 through 997. The extension completed all **488** state-prime rows: two bad-model reductions and 486 good point reductions. Its first quotient witnesses were:

| Fresh hit and beam state | First extension witness prime |
| --- | ---: |
| `hit03:D8:7` | 227 |
| `hit05:D8:5` | 239 |
| `hit07:D8:0` | 211 |
| `hit10:D8:0` | 233 |

[`extension-result.json`](extension-result.json), [`extension-rows.json.gz`](extension-rows.json.gz), and [`extension-audit.json`](extension-audit.json) preserve the extension separately. The combined 104/104 count is derived only after both independent audits pass. The original 199-cap result is not rewritten to say it certified those four states.

## Proof map and verification boundary

| Step | Lean declaration or evidence | Status |
| --- | --- | --- |
| Independent nonzero images in an exponent-two quotient force even relation coefficients | `parity_from_exponent_two_quotient` in [`AuxiliaryMod2Independence.lean`](../xedni-auxiliary-mod2-independence-20261116/AuxiliaryMod2Independence.lean) | Checked with pinned Lean and Mathlib in the earlier formalization |
| Even-coefficient descent when rational 2-torsion is absent | `auxiliary_mod2_independence` in the same module | Checked |
| Combined abstract quotient criterion | `independent_of_exponent_two_quotient` in the same module | Checked; its earlier `#print axioms` lists only standard Lean foundations |
| Exact rational models, 104 point pairs, auxiliary group orders, doubled images, good reductions, first witnesses | Census and extension results plus both independent Python audits | Checked as concrete arithmetic; these elliptic reduction maps and the prime-to-`ell` torsion-injection bridge are not Lean terms |

The checked Sage scripts reconstruct the exact rational curves and points, verify reductions to their public inputs and residual depth, then enumerate the auxiliary groups and doubled images. The Python audits independently reconstruct the rational coordinates with `Fraction`, enumerate each finite group, check every original and extension status and witness, and compare the parent digests. [`runtime-info.json`](runtime-info.json) and [`extension-runtime-info.json`](extension-runtime-info.json) record the accepted Sage runtime before each workload.

From the repository root:

```sh
./sage --runtime-info > experiments/xedni-fresh-beam-independence-20261118/runtime-info.json
./sage -python experiments/xedni-fresh-beam-independence-20261118/run.py
python3 experiments/xedni-fresh-beam-independence-20261118/audit.py
./sage --runtime-info > experiments/xedni-fresh-beam-independence-20261118/extension-runtime-info.json
./sage -python experiments/xedni-fresh-beam-independence-20261118/extend.py
python3 experiments/xedni-fresh-beam-independence-20261118/extension_audit.py
```

The extension protocol binds the **original run-result bytes**, including its elapsed-time field. Replaying the original producer changes that field and requires re-freezing the extension parent digest before rerunning `extend.py`; the committed original and extension artifacts are the immutable audit inputs. This is a certificate for the 104 fixed rational lifts under the stated prime searches. It does not establish a property of every lift rule or a relation-discovery cost.
