#!/usr/bin/env bash
set -u
control=/workspace/scratch/ct90-original-full-evaluator-native-supervisor-02
mkdir "$control" || exit 2
cp /workspace/scratch/ct90-full-evaluator-native-supervisor-02.sh "$control/original-command.sh"
date -u +%FT%TZ > "$control/start.txt"
cd /workspace/cryptanalysis || exit 2
timeout 2400 bash experiments/chained-transfer-public-target/original-full-evaluator-01/run-native-01.sh c8490c73db4cd3518435efd0ad8f60282d09ab56 /workspace/scratch/ct90-original-full-evaluator-native-02 /workspace/scratch/ct90-original-full-evaluator-build-03 > "$control/whole-worker.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$control/worker.exit"
date -u +%FT%TZ > "$control/finish.txt"
exit "$status"
