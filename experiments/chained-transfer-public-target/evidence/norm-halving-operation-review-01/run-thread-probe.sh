#!/usr/bin/env bash
set -u
p=/workspace/scratch/ct75-norm-arithmetic-review-01
timeout 30 /home/agent/.rustup/toolchains/1.99.1-x86_64-unknown-linux-gnu/bin/rustc --edition=2021 --test "$p/thread_probe.rs" -o "$p/thread-probe.bin" > "$p/thread-build.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$p/thread-build.exit"
if [[ $status == 0 ]]; then
 timeout 30 "$p/thread-probe.bin" --nocapture --test-threads=1 > "$p/thread-native.txt" 2>&1
 status=$?
 printf '%s\n' "$status" > "$p/thread-native.exit"
fi
exit "$status"
