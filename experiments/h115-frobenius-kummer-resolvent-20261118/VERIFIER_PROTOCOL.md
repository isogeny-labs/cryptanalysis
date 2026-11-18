# H115 independent verifier protocol

Freeze date: 2026-11-18

Status: source-only freeze before verifier implementation and before any H115
candidate data exist. Claims remain `[pcc:unverified]`.

## Producer binding

- crypto repository: `isogeny-labs/crypto`
- producer source revision: `6d8def5473`
- draft producer PR: `isogeny-labs/crypto#4625`
- `CURVES.json` SHA-256:
  `babd2556951ecfcaee66a5c6966364ca136bf1f62fb0a51511f391768255d295`
- `PROTOCOL.json` SHA-256:
  `c8412d94f3e6cc928c13c93572a8796cea3a983b5fcd4e6b043a75bc5b1a2363`
- `h115_sha256.rs` SHA-256:
  `4d508fe8fed91c71e0150446c53f024ff97fa8a9519d812a672ea59ef2329786`
- `h115_field.rs` SHA-256:
  `577015b44fae9828b9bddf1b2afc0403e4f44d732b3a01325f42253f0982cc82`
- `h115_producer.rs` SHA-256:
  `f0644129c8d7c0161cbddac3283f94453983d25b6f6cdeaf327b170c1fc579bd`

## Independence boundary

The verifier is a standalone Python 3 standard-library program. It does not
import, execute or translate the Rust producer. It uses tuple-valued extension
elements, Python integer arithmetic, `hashlib.sha256` and `json.loads`, and
reconstructs the frozen experiment from the five literal curve fixtures.

The producer's point, modulus, moment, channel, score, exact-ID, control,
decoder, count and digest fields are treated as untrusted claims.

## Checks to perform

1. Hash raw data-record bytes, including each trailing newline and excluding
   the final summary line. Require the producer digest, record count and raw
   byte count to match.
2. Rebuild the lexicographically first irreducible extension, `N_d`, corrected
   `N_d/r^2` cofactor, deterministic transverse point, full `r^2` torsion
   table and `r`-element `image(pi-1)=kernel(V-1)` line.
3. Recheck the Frobenius characteristic equation and
   `(V-1)(pi-1)=[r]` on the full torsion table.
4. Recompute every candidate, random-line, rational-line and coordinate-
   isomorphism moment, all 54 channels, labels and term counts.
5. Recompute all 648 predictions, row scores, global scores, exact-ID
   intersection, raw/normalized ablations, random-line selection and shuffled
   label controls.
6. For every exact ID, rerun the scalar-blind group decoder from point-keyed
   public channels and independently require reconstructed `[m]G=Q`.
7. Rerun the forbidden-oracle positive decoder separately and require 366
   checked targets.
8. Require all frozen record and cohort cardinalities. Runtime and producer
   operation counts are reported evidence, not trusted speed claims; exact
   deterministic channel-operation counts are recomputed.

## Tamper rejection

The verifier source selftest uses a synthetic, non-H115-scoring packet and
requires distinct rejection after each mutation:

1. extension coefficient;
2. Frobenius image;
3. fiber member;
4. moment;
5. scalar label;
6. predicate ID;
7. raw digest;
8. summary count.

After real evidence exists, the same eight mutations must be applied one at a
time to a copied raw packet and `--verify` must exit nonzero for every copy.
No mutation may alter the immutable raw evidence object.

## Evidence status

`--selftest` may exercise arithmetic and synthetic rejection logic, but it may
not generate a frozen H115 row or score a frozen H115 label. Only checkpointed
producer evidence from the bound crypto revision is eligible for `--verify`.
