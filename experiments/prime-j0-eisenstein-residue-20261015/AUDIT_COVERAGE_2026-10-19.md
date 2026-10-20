# Independent retained-panel ledger audit (2026-10-19)

Command:

```sh
python3 experiments/prime-j0-eisenstein-residue-20261015/audit_panels_v2.py --json
python3 -m unittest discover -s experiments/prime-j0-eisenstein-residue-20261015 -p 'test_audit_panels_v2.py' -v
```

The independent verifier inspected all 95 `.tar.gz` files in this experiment directory. It fully validated the standard raw pair ledger and its uniquely hash-matched rules for 51 archives: 5,216 runs and 2,608 pairs. For every supported archive it checks safe regular archive paths, manifest digest where recorded, run command identity against the manifest, unique run serials and identities, valid arm state, finite positive arm timings with agreement between both stored timing fields, exact pair coverage, unique reference/candidate serial assignment, recomputation of reference-time divided by candidate-time, and equality of the stored ratio to the recomputed ratio. It loads the A/A bounds only from a local JSON file whose bytes match the artifact hash recorded by that archive, then checks every declared calibration pair against those bounds.

The independent gate helper rejects malformed/non-finite/reversed intervals and only considers a directional interval (`lower > 1` or `upper < 1`) when **all** A/A rows pass. The CLI marks malformed supported ledgers as `INVALID` and exits nonzero; explicitly unsupported provenance archives remain inventoried without failing the command. Regression tests cover a forged pair ratio through the CLI, unsupported-inventory exit behavior, boolean serial rejection, invalid repetition counts, two negative times that would otherwise create a positive quotient, non-finite inputs, A/A failure blocking both above-one and below-one intervals, and both directions remaining possible after A/A passes.

This is a panel-ledger audit, not a complete reproduction of the specialized analyzers. It does not independently prove native source/binary correspondence, fixture/output semantics, host isolation, allocation provenance, compiler/runtime behavior, or the specialized bootstrap calculation. The directional helper is exercised with both interval directions, but this shared verifier does not replace a panel-specific interval recomputation. Existing panel analyzers and archived bytes remain unchanged.

## Supported archives

All listed archives passed structural ledger validation and ratio recomputation. A/A failures are listed separately below.

```text
16ad0015d96b497ca15cc3de3ce090e6.tar.gz
273359b6d2724700ad59ea1ddc978da8.tar.gz
792dca682b8d4aa799e4745fb7dd1ce9.tar.gz
alt-lazy-rotation-tier1-raw.tar.gz
alt-mixed-rows-tier1-raw.tar.gz
alt-prefetch-rep2-tier1-raw.tar.gz
alt-prefetch-tier1-raw.tar.gz
alt-radix-long10-tier1-raw.tar.gz
alt-radix-tier1-raw.tar.gz
alt-wavefront8-tier1-raw.tar.gz
c325c7ff36a74f0c8cd85db3024432f8.tar.gz
cache10-tier1-raw.tar.gz
checkpoint3-cold-tier1-raw.tar.gz
checkpoint3-online-tier1-raw.tar.gz
checkpoint5-cold-tier1-raw.tar.gz
checkpoint5-online-tier1-raw.tar.gz
checkpoint5-repeat4-cold-tier1-raw.tar.gz
checkpoint5-repeat8-cold-tier1-raw.tar.gz
horner-cold-tier1-raw.tar.gz
horner-online-tier1-raw.tar.gz
radix4033-1-raw.tar.gz
radix4033-1-replication-85e158fb-raw.tar.gz
radix4033-128-raw.tar.gz
radix4033-vs-openssl-1-raw.tar.gz
radix4033-vs-openssl-128-raw.tar.gz
radix4033-vs-openssl-fixed-table-1-raw.tar.gz
radix4033-vs-openssl-fixed-table-128-raw.tar.gz
rho-restart-hybrid-1-raw.tar.gz
rho-restart-hybrid-128-raw.tar.gz
sparse-tau-tier1-raw.tar.gz
sparse-vs-prefetch-cold-tier1-raw.tar.gz
sparse-vs-prefetch-online-tier1-raw.tar.gz
tau32-cold-tier1-raw.tar.gz
tau32-demand-cold-tier1-raw.tar.gz
tau32-digit-graph-1-raw.tar.gz
tau32-digit-graph-128-raw.tar.gz
tau32-online-tier1-raw.tar.gz
tau32-projective-1-raw.tar.gz
tau32-projective-1-v2-raw.tar.gz
tau32-projective-128-raw.tar.gz
tau32-projective-128-v2-raw.tar.gz
tau32-rotated-step-1-raw.tar.gz
tau32-rotated-step-128-raw.tar.gz
tau32cp5-batch1cold-tier1-raw.tar.gz
tau32cp5-batch4096cold-tier1-raw.tar.gz
tau32cp5-cold-tier1-raw.tar.gz
tau32cp5-online-tier1-raw.tar.gz
tau64-cold-tier1-raw.tar.gz
tau64-online-tier1-raw.tar.gz
tier1-mixed76-run1-raw.tar.gz
tier1-mixed76-run2-raw.tar.gz
```

## A/A failures found

These 15 supported archives have at least one raw calibration ratio outside that archive's declared A/A window. The shared gate therefore does not allow either directional qualification for these panels, regardless of which side of one a comparison interval lies on.

```text
alt-prefetch-tier1-raw.tar.gz
alt-radix-long10-tier1-raw.tar.gz
alt-radix-tier1-raw.tar.gz
c325c7ff36a74f0c8cd85db3024432f8.tar.gz
cache10-tier1-raw.tar.gz
checkpoint3-cold-tier1-raw.tar.gz
radix4033-vs-openssl-fixed-table-1-raw.tar.gz
radix4033-vs-openssl-fixed-table-128-raw.tar.gz
rho-restart-hybrid-1-raw.tar.gz
sparse-vs-prefetch-cold-tier1-raw.tar.gz
tau32-cold-tier1-raw.tar.gz
tau32-demand-cold-tier1-raw.tar.gz
tau32cp5-cold-tier1-raw.tar.gz
tau64-cold-tier1-raw.tar.gz
tier1-mixed76-run1-raw.tar.gz
```

## Unsupported retained archives

These 44 archives were inventoried but not included in the shared ratio/A/A audit:

```text
1068b7066ae148de9edfab8aff9075c0.tar.gz
alt-hybrid-native-provenance.tar.gz
alt-lazy-rotation-native-provenance.tar.gz
alt-mixed-rows-native-provenance.tar.gz
alt-prefetch-native-provenance.tar.gz
alt-radix-long10-native-provenance.tar.gz
alt-radix-native-provenance.tar.gz
alt-wavefront8-native-provenance.tar.gz
cache10-native-provenance.tar.gz
checkpoint3-online-native-provenance.tar.gz
checkpoint5-online-native-provenance.tar.gz
checkpoint5-repeat8-native-provenance.tar.gz
eisenstein-gauge-projective-native-provenance.tar.gz
eisenstein-montgomery-native-provenance.tar.gz
eisenstein-packed-gauge-native-provenance.tar.gz
eisenstein-pair-fixed-provenance.tar.gz
eisenstein-pair-native-provenance.tar.gz
horner-cold-native-provenance.tar.gz
horner-native-provenance.tar.gz
horner-online-native-provenance.tar.gz
mixed640-compile-fixtures-20261016.tar.gz
openssl-secp256k1-native-provenance.tar.gz
pair-accumulation-native-provenance.tar.gz
radix4033-128-pilot-raw.tar.gz
radix4033-fixed-table-full-replay-raw.tar.gz
radix4033-full-replay-raw.tar.gz
radix4033-native-provenance.tar.gz
rho-closeout-confirmation-source.tar.gz
rho-restart-hybrid-native-provenance.tar.gz
rotation-cache-profile-native-provenance.tar.gz
sparse-tau-native-provenance.tar.gz
sparse-vs-prefetch-cold-native-provenance.tar.gz
sparse-vs-prefetch-online-native-provenance.tar.gz
tau32-demand-full-replay-raw.tar.gz
tau32-demand-native-provenance.tar.gz
tau32-digit-graph-full-replay-raw.tar.gz
tau32-digit-graph-native-provenance.tar.gz
tau32-native-provenance.tar.gz
tau32-projective-full-replay-raw.tar.gz
tau32-projective-native-provenance.tar.gz
tau32-rotated-step-full-replay-raw.tar.gz
tau32-rotated-step-native-provenance.tar.gz
tau32cp5-native-provenance.tar.gz
tau64-online-native-provenance.tar.gz
```

The provenance and fixture archives lack the standard panel ledger. The one-case pilot/replay archives lack a unique matching rules document and do not provide the calibration cases required by this gate. `1068b7066ae148de9edfab8aff9075c0.tar.gz` has a standard ledger, but its referenced rules artifact is not present locally with matching bytes; it is deliberately left unsupported rather than assigned another panel's thresholds.
