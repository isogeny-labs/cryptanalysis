---
name: queue-experiment
description: Submit a protocol-bound experiment to remote capacity and get its data back as a unified export - a measurement job to a host that can earn a Tier 0/1 receipt, a throughput, search or training job to the cheapest spot or pod capacity with a checkpoint that survives interruption. Pointer to the canonical skill in aburan28/crypto; here the backends are cloud/modal_run.py, cloud/runpod_pod.py, cloud/cairn_queue.py, cloud/fleet.py and deploy/aws/launch.py.
---

# Queue an experiment (pointer)

The canonical skill and design are in `aburan28/crypto`:
`.agents/skills/queue-experiment/SKILL.md` and
`taskq/deploy/spot-checkpoint/README.md` (the job envelope, the two
queues, the application and CRIU checkpoint routes, and what a restore
means for a row). Read them and follow them. This repository's `AGENTS.md`
"Remote compute" and "Run index calculus on a GPU" still decide which of
its own launchers to use and what each run record must carry.

## In this repository

| protocol `measurement_class` | backend here | checkpoint |
|:--|:--|:--|
| `measurement` (a clock or counter against an A/A interval) | the taskq `cpu-exclusive` pool or EKS Iso Lab in crypto for a Tier 0/1 receipt; a Runpod pod (`cloud/runpod_pod.py`, `cloud/fleet.py run`) earns at most Tier 1 and only with the paired receipt | none; an interrupted row is a new row |
| `throughput`, `search`, `training` | `cloud/modal_run.py run --shards K --detach` (one envelope per shard, `SHARD_INDEX`/`SHARD_COUNT`), `cloud/cairn_queue.py submit` (one receipt per job), `deploy/aws/launch.py` with `--spot` where offered | application manifest generations under `$CHECKPOINT_DIR`, synced to the job's `--out` or S3; `cloud/job_runner.sh` and `cloud/modal_run.py status` give the `status.json` each row copies its host from |

- Every shard's `status.json` (exit code, wall, host, CPU count, GPU names)
  goes into the export row's host and isolation fields; a Modal sandbox's
  `/proc` shows the host, so quote the requested `--memory`.
- A GPU run records its `gpu` block; `gpu.devices` empty is a CPU-only row
  and is labelled one.
- A resumed shard keeps its counts and loses its clock (`wall_valid:
  false`); a timeout or OOM is a row, never a retry.
- Stop or delete every pod and sandbox you start; never write credentials
  into the tree.
