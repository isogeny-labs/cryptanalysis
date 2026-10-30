# Prepared next discriminator: fully priced fixed-base log preparation

Status: implemented workload, not executed on an accepted benchmark host.
This stage comparison does not measure a full IC solve or prove a lower bound
against all generic methods. Its execution is blocked by missing CUDA-host
capability in the selected environment, under the repository benchmark rule.

Freeze the existing large-f6 curve, generator, r=206477 and64 projected base
points (32 folded columns). Compare generic pair reuse with Hecke+pair reuse.
Both arms start from the same explicitly supplied base, not an uncharged
factor-base search. Base generation is outside this fixed-base workload and
must be added for any full-pipeline claim. File loading, imports and target
fixture construction are outside this stage window, recorded as exclusions.

Charge the Hecke arm for finite-field modular-function reconstruction and
degree2/3 fiber construction, group checks, cofactor projection and folding.
The generic arm does not construct those functions. Both then charge the
complete signed pair index, coefficient bookkeeping, collision-basis handling,
relation LA, BSGS table construction, generic free-log queries, pivot recovery,
and replay of every prepared base label. Record exclusive wall/process times,
group counters and residual overhead. Zero-cost geometric or LA phases are
not assumed. All answers must equal the independently replayed source labels.

Use a tuned shared BSGS table with m=min(4096,r,max(1,floor(sqrt(r*k/2))+1)),
where k is the number of free logs. Both arms have the same4096-entry table
cap and the same point-index memory policy. The tuning rule is frozen before
measurement; the generic arm is not forced to use the weaker sqrt(r) table
from earlier correctness studies. A stronger generic collector may still beat
this declared control and must not be claimed ruled out.

Full independent pair-stream re-enumeration and a third rank check are a
separately reported certificate phase outside the preparation window. Replay
of the actual recovered labels remains inside. Retain code/input hashes,
raw phase times, CPU time, peak process RSS, GPU/device information, point-set
identity and all unsuccessful rows. No ratios are qualified by this workload
alone; an accepted benchmark harness must supply allocation/isolation,
calibration, alternating repeated pairs, A/A and positive controls.

Run cost_cell.py --arm generic|hecke --out UNIQUE_PATH only after checkpoint
and GPU preflight. Each invocation is one fixed-base workload, not a batch
of DLP targets. The initial600-second cap applies. Preserve its fail-closed
no-GPU record here. Fresh public-target descent and matched strong rho remain
separate downstream requirements for any online IC speed claim.
