<!--
Canonical security, disclosure and acceptable-use policy for isogeny-labs
repositories (action plan F4, docs/strategy/2026-11-21-action-plan.md).
Copy it into a repository as SECURITY.md, then fill the two marked sections.
Owner actions before the first copy merges:
  1. enable GitHub private vulnerability reporting on each public repository
     (Settings > Code security > Private vulnerability reporting);
  2. create the security@isogenylabs.io mailbox, or replace the address below.
This is a policy draft, not legal advice. Counsel reviews it with F6 and F9.
-->

# Security policy

## Reporting a vulnerability

Please report security problems privately. Do not open a public issue.

- **GitHub:** use "Report a vulnerability" on this repository's Security tab.
- **Email:** security@isogenylabs.io

Tell us what you found, how to reproduce it, and what you think the impact
is. We confirm receipt within 3 business days and tell you what we will do
within 10 business days. Our default is coordinated disclosure after
90 days, or sooner once a fix is released. We credit reporters who want to be
credited.

We will not pursue legal action against good-faith research that stays
within this policy: it avoids privacy violations, data destruction and
service disruption, uses only accounts and data you own or are authorised
to use, and gives us reasonable time to respond before anything is made
public.

## What this repository is, and what it is not

cryptanalysis is Isogeny Labs' open research library for measuring what
cryptanalytic attacks cost. It has two parts: a C11 discrete-log library
(`src/`, `include/`) that works only in groups over 64-bit primes, and the
Rust attack suite (`suite/`, command `crax`), which implements published
attacks on symmetric ciphers, hash functions, ECDSA nonces, RSA keys,
elliptic-curve and finite-field discrete logarithms and the NIST
post-quantum schemes, plus CUDA, Metal and FPGA kernels for the public
Certicom challenges. None of it is constant-time or audited, and none of it
protects anything (`suite/README.md`): do not use its primitives in
production. Several components recover keys. They exist to measure attacks
and to let owners test their own keys, signatures and implementations. The
table below lists them with their safeguards, and the suite README's
"Defensive use of `ecdsa_audit`" says who should run the ECDSA transcript
auditor, on what data and with what authorisation. Third-party code and
patches are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Acceptable use

Some code here implements published cryptanalytic techniques: attacks on
weak parameters, key recovery from flawed signatures or leakage, and network
probes that read how a system negotiates cryptography. We publish it for
research, education, and defensive assessment.

- Use it only on systems, keys, signatures and data that you own, or that
  you have written authorisation to test.
- Do not use it to obtain anyone else's keys, funds, messages or data, or to
  get into systems you are not authorised to access.
- Network probes complete ordinary handshakes and read what the server
  offers. Do not point them at networks you do not operate or have
  permission to assess, and respect the target's rate limits.
- If you recover key material that is not yours, stop. Do not use it or
  share it; report it privately as above.

## How Isogeny Labs runs client engagements

When we assess a client's systems, these rules hold whatever the contract
says on top of them:

1. **Written authorisation first.** No active test starts before a signed
   authorisation that names the systems, the adversary model, what counts as
   a finding, the testing window and the client's emergency contact.
2. **Public data by default.** We analyse public material (signatures, public
   keys, certificates, handshakes) unless the client agrees in writing to
   provide more.
3. **Recovered key material.** If an analysis recovers a private key or
   other secret, we tell the client's named contact at once through the
   agreed secure channel. We never store it in plaintext, never put it in a
   repository, ticket, report or log, and delete it at the end of the
   engagement, confirming the deletion in writing.
4. **Evidence, not exploitation.** We show a finding with the smallest proof
   that establishes it: a verified result, a test, a signed evidence record.
   We do not use it beyond that.
5. **Third parties.** A weakness found in someone else's product is reported
   to that vendor under coordinated disclosure (90 days by default), with
   the client's agreement where the client's data was involved.

## Ethics

We build attacks so that their cost is measured rather than guessed, and so
that weak deployments are found by their owners first. We do not sell attack
capability, target individuals, or take work whose purpose is to defeat
security that people rely on without their owner's consent.

## Components with dual-use capability

Suite module paths are relative to `suite/src/cryptanalysis/` unless written
in full.

| Path | What it does | Intended use | Safeguards |
|:--|:--|:--|:--|
| `suite/src/cryptanalysis/ecdsa_audit.rs`, `signature_corpus.rs` (`crax ecdsa audit`) | Scores an ECDSA signature transcript for nonce bias and reuse; if it finds bias, recovers the private key to prove it | Defensive audit of a signer you own or are authorised to assess | Works only on the `(r, s, z)` and public key the caller supplies; checks the key against the public key. A `key_recovered` report prints the key: handle it under the rules above |
| `hnp_ecdsa.rs`, `multi_key_hnp.rs`, `bleichenbacher.rs`, `lattice.rs` (`crax ecdsa nonce-reuse`, `crax ecdsa hnp`) | Key recovery from a reused nonce or from biased nonces (hidden-number problem, LLL/BKZ) | Measuring and demonstrating nonce-generation failures | Public signature data the caller supplies; every recovered key is checked against the public key; `--demo` plants its own key |
| `invalid_curve_attack.rs` (`crax ecdsa invalid-curve`) | Recovers a scalar from an implementation that skips point validation, using points on weak twists | Testing your own ECDH or scalar-multiplication code | Queries an in-process oracle built from `--secret`; twist enumeration is `O(p)`, so only toy-size base primes are practical |
| `factoring/rsa_attacks.rs`, `factoring/` (`crax rsa ...`, `crax factor`, `gnfs`, `qs`, `ecm`) | Fermat, Wiener, Håstad broadcast, common modulus, small-`e` root, batch GCD, `(n, e, d)` to `p, q`; QS, NFS and ECM factoring | Screening RSA keys for structural mistakes; teaching factoring | The screens read public moduli and exponents. The general-purpose factoring is educational and reaches tens of digits, far below deployed RSA sizes (`suite/README.md`) |
| `ml_kem_pco.rs`, `ml_dsa_leakage.rs`, `ml_dsa_fault.rs` (`ca-suite mlwe kem-pco`, `dsa-leak`, `dsa-fault`) | Key recovery for ML-KEM from decapsulation leakage and for ML-DSA from mask leakage or faulted masks | Showing implementers what a leak or fault costs | Oracles, leakage and faults are simulated in-process from a key the caller already holds, against the crate's own FIPS 203/204 code. No trace acquisition, fault injection or device interface |
| `aes/dpa.rs`, `aes/cache_timing.rs` | Correlation power analysis and cache-timing attacks on AES | Teaching and measurement | Simulated traces and timings only |
| `md5_chosen_prefix.rs`, `md5_differential.rs`, `md5_hashclash_ffi.rs` | MD5 collision search; bindings for HashClash chosen-prefix collisions | Hash-function research | The HashClash binding is scaffolding and links nothing in any build (THIRD_PARTY_NOTICES.md) |
| `cuda/`, `bindings/rust/cryptanalysis-cuda/` | GPU Pollard rho for the C library | Measuring rho constants on a GPU | Same 64-bit groups as the C library |
| `ecc2k130/`, `gpu/certicom/`, `fpga/` | CUDA, Metal and CPU rho clients and an FPGA walker for the Certicom ECC2K-130, ECC2-131 and ECCp-131 curves | The public Certicom challenges | Fixed to the published challenge curves and points; the FPGA design has been checked only in simulation |
| `suite/cuda/` | GPU F4 over GF(2) and point-decomposition kernels | Index-calculus research | Research kernels on benchmark instances; no key input |
| `src/`, `include/cryptanalysis/` (rho, BSGS, kangaroo, Pohlig–Hellman, index calculus, Cheon) | Generic discrete-log solvers | Measuring algorithm constants; the reference implementation | Groups over 64-bit primes only, by design: "not an attack tool for cryptographic sizes" (`README.md`) |
| `include/cryptanalysis/ca_coord.h`, `bindings/go/cmd/ca-coordinator/`, `suite/src/cryptanalysis/pollard_collab/` | Distributed Pollard rho: a coordinator and agents, or peers gossiping over TCP | Pooling cooperating machines on one rho instance | Connects only to the coordinator or peers its operator names; scans and probes nothing |
