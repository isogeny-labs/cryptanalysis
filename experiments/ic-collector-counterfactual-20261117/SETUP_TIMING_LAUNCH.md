# Reviewable timing allocation request

The completed correctness-only allocation is terminal0; no owned worker remains. Native admission is unsigned PCC-20261117-a665d2. This is a separate request for one timing allocation; the earlier approval does not authorize it. [pcc:unverified]

The full protocol is FRESH_SETUP_PROTOCOL.md. Its runner, analyzer, replayers, provenance sealer, metric/raw-reference drivers and200public workload identities are published before execution. The8methods include the3frozen paths and5new-binary controls. The benchmark record benchmarks/records/20261117T1809Z-ic-collector-buffer-state-eightpath-001.json was initialized before timing and remains open, with no results or metrics. The progress exporter currently emits zero values for this record.

Requested bound: one Modal CUDA-image L4 allocation,4CPUs,8GiB,900seconds, one shard, CPU arithmetic on one exposed CPU; controller780seconds, child12seconds, native preflight30seconds. No replacement allocation, retry, observer or extra profiling is included. All failed A/A rows, caps and incomplete effects remain. This is an exploratory comparison and cannot qualify itself or establish a physical allocator/cache mechanism.

After explicit approval, require a clean pushed source revision, rerun checkpoint_gate.py and verify its remote restore receipt, then launch exactly:

```sh
python3 cloud/modal_run.py run --image cuda --gpu L4 --cpu 4 --memory 8 --timeout 900 --shards 1 --out experiments/ic-collector-counterfactual-20261117/timing-setup-001 --detach -- python3 experiments/ic-collector-counterfactual-20261117/run_setup_fresh.py
```

Collect the one job to completion. Preserve the launch metadata immediately, then use analyze_setup_fresh.py, replay_setup_fresh_answers.py, replay_setup_fresh_states.py and seal_setup_provenance.py. Initialize no replacement record or workload after seeing results. bind_setup_record.py imports the original native hardware/source/timestamps while requiring that the existing record predates execution; coordinator capture remains retained. Write all180declared metrics only for a complete analyzed panel; retain incomplete outcomes without invented values. Upload/read back every raw reference before closure. A full report/plots/PDF and exact progress export replay are required after execution. The broader optimization goal remains open. [pcc:unverified]
