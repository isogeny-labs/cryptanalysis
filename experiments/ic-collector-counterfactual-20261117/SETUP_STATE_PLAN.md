# Prospective local preparation-state controls

Question: does restoring the old point-buffer reservation or gather traffic, while retaining indexed arithmetic and exact table contents, explain the collector-clock contrast? This is a mechanism test; no improvement is assumed. [pcc:unverified]

Keep existing staged(5) and indexed(3) paths unchanged. Add three explicit controls in the same binary: indexed with an opaque observation of empty point buffers(6), indexed with the same observation plus chunk-sized point-buffer capacities(7), and indexed with the observation plus capacities and original ordered point gathers(8). Each observes the buffers before each flush so the compiler cannot silently remove the intended reservations/writes. The observation is shared by all three new cells; compare3/6 for its effect before attributing6/7 or7/8. These are experimental controls, never automatic defaults. All preserve the14-entry indexed counter schema, indices/chunks, map insertion, arithmetic and queries.

Prediction: a repeatable reserve or gather contrast that restores collector timing narrows the preparation-state explanation; absence of a contrast rejects that factor as sufficient. Lower setup cost alone does not establish a collector remedy or charged primary gain. Neither clock nor Callgrind identifies a physical cache/allocator cause without additional evidence. [pcc:unverified]

Local admission first: chunks1,7,64,1024; complete map and first-witness comparison against scalar/staged/indexed; counts match indexed; invalid control/chunk rejection; portable fallback retained; strict library/probe Clippy. Use the archived16-source recipe and declared3-file overlay. Two Cargo jobs,240seconds per command, retain every failed/capped log; no local performance claim. No new cloud allocation is authorized by this local plan. Before native timing freeze a separate protocol, identities, transfer control, A/A, matched rho, all outcomes and explicit allocation budget.

Native admission proposal (requires a new bounded allocation): one Modal CUDA-image L4 allocation,4CPUs,8GiB,900seconds, one shard; CPU arithmetic only. Run build_setup_native.py, retaining setup-build-001 and setup-cell-smoke-001. Reconstruct the exact archived source recipe, retain compiler/environment matching, require positive AVX2/PCLMUL use in all five fields,15additional complete setup-control maps per field, existing walker/inverse/packed/const controls,20synthetic-unit pipeline answers and strict lint. Retain cap/failure as such; no retries, replacement host, fresh target timing or speedup claim under this proposal. Native instruction diagnostics and fresh timing need a subsequent prospective protocol. [pcc:unverified]

Reviewable launch:

```sh
python3 cloud/modal_run.py run --image cuda --gpu L4 --cpu 4 --memory 8 --timeout 900 --shards 1 --out experiments/ic-collector-counterfactual-20261117/setup-build-001 --out experiments/ic-collector-counterfactual-20261117/setup-cell-smoke-001 --detach -- python3 experiments/ic-collector-counterfactual-20261117/build_setup_native.py
```
