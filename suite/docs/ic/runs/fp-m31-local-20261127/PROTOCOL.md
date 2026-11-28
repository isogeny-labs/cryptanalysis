# Corrected M31 prime-field local protocol

The requested field is Fp with p=2147483647=2^31-1. Use the existing native
prime-field-auxiliary-ic crate and ca-ic auxiliary CLI; summands are2,3,4.
Earlier binary/31-summand runs are not part of this experiment.

Reference curve from native cdclt_ct186_audit.rs: y^2=x^3+2x+14, order
N=2147505293, generator(1,814455902). Verify subgroup membership natively.
Do not confuse coordinate modulus p with scalar modulus N. Local CPU-only
runs and local artifact storage remain explicitly authorized by the user.
No new PCC claim IDs or qualified performance claims will be created.

## Inputs, seeds and cases

seeds.json is frozen before outcomes. Domain-separated SHA256 derives64-bit
streams for each of2 independent public synthetic targets, sampler, and
factor-base construction. The native fixture helper alone receives a target
scalar. Its public JSON has only curve/group parameters, G and Q coordinates,
and interval abscissae; evaluator scalar data remains outside solver inputs.
Every paired arm receives the same public input file and sampler seed.

Use3 native base configurations: norm-one torus depth7 with auto backend,
the identical torus base through direct_control (scalar), and direct interval
x=0..127. Structured/direct torus arms must have matching column hashes.
The interval arm changes factor-base selection; no same-base speed claim.

1. Existing native release tests multi_summands, random_control, pipeline
   supply finite-control and arithmetic/certificate checks before M31 runs.
2. Positive PDP controls: sum first m native base representatives, m=2,3,4,
   for each base. Check the returned row and repeat every configuration once
   to compare mathematical output, not timing. These planted controls are
   not relation-probability or discrete-log recovery measurements.
3. For both ordinary Q targets, run each m/base in fixed-prefix yield mode:
   max_queries512, walk_lanes4, max_millis1500. Retain capped prefixes; only
   equal completed prefixes permit paired yield comparison.
4. Same ordinary cases in solve mode: max_queries65536, walk_lanes4,
   max_millis2000, max_proof_nodes1048576, native default relation cap.
5. Strong native rho references on both ordinary Q targets: use direct
   interval base, one IC query, and rho_max_ops200000. The separate native
   rho result must replay Q from its recovered scalar.

Every process has20 seconds and2GiB RSS. Keep all failures, soft limits,
resource kills and native reports. Build/setup, online and replay intervals
remain separate. CLI status solved/relation_found may return exit1 in this
revision; preserve that code and classify the explicit native JSON instead
of calling a completed mathematical report a crash. Do not compare timings
across the release fixture helper and debug solver. No threshold relaxation.

This is a descriptive single-host diagnostic, not a registry promotion or
rho-parity test. Raw reports and hypotheses remain [pcc:unverified].
