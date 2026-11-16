#!/usr/bin/env bash
# Self-test of the Lean proof gate: every fixture under pass/ must pass and
# every fixture under fail/ must fail, and the gate's output must match the
# fixture's first line, `-- expect: <ERE>`. Checking the reason matters: a
# broken audit makes every fail/ fixture fail too, for the wrong reason. Runs in CI on every gate trigger, so the
# gate is exercised even in a repository with no Lean proofs yet.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(git -C "$here" rev-parse --show-toplevel)
gate="$here/../proof-gate.sh"
cd "$root" || exit 3
rel=${here#"$root"/}
bad=0
for f in "$here"/pass/*.lean "$here"/fail/*.lean; do
  want=pass; case "$f" in */fail/*) want=fail ;; esac
  LEAN_GATE_TRUSTED="$here/trusted-native.txt" "$gate" "$rel/$want/$(basename "$f")" > /tmp/lean-selftest.$$ 2>&1
  rc=$?
  got=pass; [ $rc -eq 1 ] && got=fail; [ $rc -ne 0 ] && [ $rc -ne 1 ] && got="error($rc)"
  expect=$(sed -n '1s/^-- expect: //p' "$f")
  if [ -z "$expect" ]; then echo "WRONG no '-- expect:' line: $(basename "$f")"; bad=1; continue; fi
  if [ "$got" = "$want" ] && grep -qE -- "$expect" /tmp/lean-selftest.$$; then
    echo "ok    $want  $(head -1 /tmp/lean-selftest.$$)"
  else
    echo "WRONG expected $want matching /$expect/, got $got: $(basename "$f")"; cat /tmp/lean-selftest.$$; bad=1
  fi
done
# Projects with an unimported source must not inherit a default-root pass.
# An unregistered source is privately compiled and audited; a valid source
# passes, while `sorry` fails the audit even when Lake's default target passes.
projects=$(mktemp -d)
trap 'rm -rf "$projects"' EXIT
for control in omitted unconfigured-good configured-good configured-bad; do
  project="$projects/$control"
  mkdir -p "$project"
  git -C "$project" init -q
  pin="$root/lean-toolchain"
  [ -f "$pin" ] || pin="$here/../lean-toolchain"
  cp "$pin" "$project/lean-toolchain" || exit 3
  cat > "$project/lakefile.toml" <<'EOF'
name = "GateControl"
defaultTargets = ["Root"]
[[lean_lib]]
name = "Root"
EOF
  echo 'theorem rootTrue : True := by trivial' > "$project/Root.lean"
  if [[ "$control" = *-good ]]; then
    echo 'theorem omittedTrue : True := by trivial' > "$project/Omitted.lean"
  else
    echo 'theorem omittedFalse : False := by sorry' > "$project/Omitted.lean"
  fi
  if [[ "$control" = configured-* ]]; then
    printf '\n[[lean_lib]]\nname = "Omitted"\n' >> "$project/lakefile.toml"
  fi
  git -C "$project" add .
  (cd "$project" && "$gate" --out receipts .) > /tmp/lean-selftest.$$ 2>&1
  rc=$?
  case "$control" in
    omitted) want_rc=1; expect='FAIL_audit' ;;
    unconfigured-good) want_rc=0; expect='PASS +2 thm' ;;
    configured-good) want_rc=0; expect='PASS +2 thm' ;;
    configured-bad) want_rc=1; expect='FAIL_audit' ;;
  esac
  if [ "$rc" -eq "$want_rc" ] && grep -qE "$expect" /tmp/lean-selftest.$$; then
    echo "ok    $control $(head -1 /tmp/lean-selftest.$$)"
  else
    echo "WRONG project $control expected $want_rc /$expect/, got $rc"
    cat /tmp/lean-selftest.$$
    bad=1
  fi
done
# A Lake default target can omit a registered Lean module. The gate must
# explicitly build and audit the omitted tracked source before passing.
for project in "$rel/project-omitted" "./$rel/project-omitted" "$rel/project-omitted/" "$rel/project-quoted"; do
  LEAN_GATE_TRUSTED="$here/trusted-native.txt" "$gate" "$project" > /tmp/lean-selftest.$$ 2>&1
  rc=$?
  if [ "$rc" -eq 1 ] && grep -q 'FAIL_audit' /tmp/lean-selftest.$$ && \
     grep -q 'sorryAx' /tmp/lean-selftest.$$; then
    echo "ok    fail  $project (tracked source audited)"
  else
    echo "WRONG $project: expected FAIL_audit for sorryAx, got exit $rc"
    cat /tmp/lean-selftest.$$
    bad=1
  fi
done
rm -f /tmp/lean-selftest.$$
[ $bad -eq 0 ] && echo "gate self-test passed" || echo "gate self-test FAILED"
exit $bad
