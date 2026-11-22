# Durable compute for the a=0 native genus-two full solve

The canonical investigating problem and its acceptance criteria are maintained
in [crypto's resource record](https://github.com/aburan28/crypto/blob/codex/binary-genus2-cover-20261014/problems/binary-genus2-a0-full-solve-compute.md).

The current worker has executable, resumable native searches for the complete
prime subgroups. The a=0 full solve remains outstanding; its short-prefix
birthday-scale work projection is months on one fully occupied core, not an
actual solve duration or a proved lower bound. Durable checkpoint retention
and actual independently verified full-target recoveries remain required.
The [study](../research/binary_genus2_speed_20261014/REPORT.md) republishes the
same frozen performance evidence as crypto, not an independent campaign.

The [completed a=1 panel snapshot](../research/binary_genus2_speed_20261014/runs/run-20261014T2250Z/ARCHIVE.md)
adds the final a=1 native full target (eight now complete) and retains all a=0
checkpoint tables without candidates. This leaves the durable-compute and
actual a=0 full-recovery exit criteria unmet; status remains investigating.


### 2026-10-19: actual interruption and exact checkpoint recovery

The original PID 21441 was absent after environment reconnection. Its last
retained progress was dated 2026-10-17 01:20:27 UTC; the disappearance time is
unknown. After confirming there was no other campaign worker, the original
immutable binary resumed the full saved collision tables, lanes and public
jobs as PID 641/start tick 23288. All 16 public job files byte-match the latest
frozen archive. [The operational receipt](../research/binary_genus2_speed_20261014/maintenance/20261019-resume-ci/README.md)
records the backup hashes, acknowledged pause and subsequent advancing work.

The three repeated a=1 Q_7 verification records are replay rows, not new
solves: there remain 24 unique a=1 completions and zero a=0 completions.
Latest full checkpoints and their backup remain workspace-local without a
durable-retention guarantee. The interruption/resume does not meet either
exit criterion, supply a continuous-host timing, or close this problem.
