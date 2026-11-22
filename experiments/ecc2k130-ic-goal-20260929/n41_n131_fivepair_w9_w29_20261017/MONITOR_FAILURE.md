# First N41 join monitor failure and terminal recovery

The first `run_join.py` invocation launched the frozen `join_five` worker,
then raised `PermissionError: [Errno 1] Operation not permitted` while
`psutil.Process.children(recursive=True)` asked macOS `sysctl` for the
system process list. This occurred after launch, so the parent monitor
did not write `join_result.json` or record the worker's exit code. The
worker's raw stdout and stderr were already bound to files in this directory.

Read-only process inspection confirmed native PID `13942` running with
858,448 KiB RSS at elapsed 11 seconds. Direct `psutil.Process(13942)`
reported 1,186,283,520 bytes RSS later. After the worker finished,
the same PID returned `NoSuchProcess`. Its frozen stdout contains
`CHECK_PASS 1420`, `LEFT_DONE 21868032`, and
`MISS_COMPLETE 79424 0 20.3124`; stderr is empty. The independent
`seal_single.py` recounts all 21,868,032 column-disjoint left triples
and 79,424 right pairs from the saved source table, and records the
complete single-raw-orientation miss in `single_result.json` with the
exit code explicitly unknown.

The subsequent orbit experiment has a separate source, binary, protocol,
stdout, stderr, and result. Its runner monitors the direct native PID and
does not request a global process list.
