# N83 E-1 capacity replay on a Tier 1 RunPod CPU Pod

This replay runs the same four-million-state, 1,024 MiB sampled peak-RSS
gate on the stopped RunPod CPU Pod `thyvmdqmzsz5ik` once it is resumed.
The RunPod API reported 8 vCPUs, 16 GiB memory, zero GPUs and $0.24 per
running hour for that allocation. The protocol caps active Pod time at
5,400 seconds, an estimated $0.36 compute charge at that reported rate,
and requires stopping the Pod immediately after receipts or an operational
failure. The Pod is a Tier 1 cloud instance: it does not supply physical
host isolation.

The [protocol](protocol.json) fixes hash, split, split, hash order on one
public N83 point and the same Q1325 base/state permutation as the local
capacity panel. It pins the `cryptanalysis` experiment source and the
separate public `crypto` repository at commit
`46416a4129c299dad4b1fd62d1a620dbd0d34317`. The worker is
byte-identical to the five-test split-slot implementation. Run records
include exposed CPU affinity, cgroup CPU/memory limits, throttling deltas,
host steal-time delta, CPU frequency if available, and before/after
calibration. All first attempts, caps and infrastructure failures are
retained. A capped arm has no target-stage runtime or assigned relation
yield.

The exact field modulus is `z^83+z^7+z^4+z²+1`, which differs from the
primary retained-base sweep's polynomial representation. The replay is a
root-index capacity result. `candidate_id` and complete single-target
IC/rho online speedup remain null.

Prepare and push the protocol before resuming the Pod:

```sh
N83_CRYPTO_ROOT=/path/to/clean/crypto-commit-46416a4 python3 run.py --prepare
```

On the Pod, check out the pinned public repositories in the declared
locations, install the locked Rust toolchain, and run:

```sh
RUNPOD_POD_ID=thyvmdqmzsz5ik python3 run.py --run
```

Save all raw files and the host receipt before stopping the Pod. The
independent audit and result table are added after the first-attempt calls.
