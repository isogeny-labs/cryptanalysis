#!/usr/bin/env bash
# Repository-wide Lean proof gate (AGENTS.md "Mathematical results should
# include Lean proofs").
#
# For every Lean target in the repository:
#   * a Lake project (a directory with lakefile.toml / lakefile.lean): `lake build`,
#     explicitly build every tracked Lean source, then audit every built module;
#   * a standalone .lean file outside any Lake project: compile it with `lean -o`
#     against the core library, then audit that module.
# One frozen historical failed source is checked as an expected-failure target
# by exact source hash and diagnostic; see tools/lean/README.md.
# The audit (AuditAxioms.lean, next to this script) fails any theorem whose transitive
# axioms go beyond propext / Classical.choice / Quot.sound: `sorry`,
# `native_decide` and user axioms all fail. A target with no theorems fails too.
#
# Shipped by the CryptoLean package. A consumer runs its pinned copy from its
# own repository root:  .lake/packages/CryptoLean/tools/proof-gate.sh
# The repository checked is the one containing the current directory, and its
# trust manifest is tools/lean/trusted-native.txt there (override with
# LEAN_GATE_TRUSTED; a missing file means nothing is trusted).
#
# Usage: proof-gate.sh [--list] [--out DIR] [TARGET ...]
#   TARGET is a project directory or standalone file (default: all discovered).
#   --list prints the discovered targets and exits.
#   --out DIR writes one receipt per target (build log, audit log, status).
# Exit status: 0 all targets pass; 1 some target failed; 3 infrastructure error.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
root=$(git rev-parse --show-toplevel) || exit 3
audit="$here/AuditAxioms.lean"
trusted="${LEAN_GATE_TRUSTED:-$root/tools/lean/trusted-native.txt}"
# This retained first attempt is a negative control, not a claimed proof.
# Keep the exact source and expected diagnostic pinned so changing either one
# cannot silently turn an unrelated build failure into a passing target.
archived_failed='research/isogeny_world_frontier_20261016/replay-optimization-v1/implementation-01/Newton.failed.lean'
archived_failed_sha256='b439d1edbe04798a56012688254ea7bd120494e4fd10856f4bdc0c07796e9d1c'
# shellcheck disable=SC2016 # The Lean diagnostic contains literal backticks.
archived_failed_error='error(lean.unknownIdentifier): Unknown constant `Int.mul_two`'
trust_args=()
[ -f "$trusted" ] && trust_args=(--trusted "$trusted")
out=""
list=0
targets=()
while [ $# -gt 0 ]; do
  case "$1" in
    --list) list=1 ;;
    --out) out=$2; shift ;;
    *) targets+=("$1") ;;
  esac
  shift
done

discover() {
  cd "$root" || exit 3
  # Lake projects: every lakefile outside build output and vendored packages.
  git ls-files -- '*lakefile.toml' '*lakefile.lean' | grep -v '^tools/lean/selftest/' \
    | xargs -r -n1 dirname | sort -u
  # Standalone files: tracked .lean files with no lakefile in any parent directory.
  git ls-files -- '*.lean' | grep -vE '^tools/(lean|selftest)/' | while read -r f; do
    d=$(dirname "$f")
    while [ "$d" != "." ] && [ ! -f "$d/lakefile.toml" ] && [ ! -f "$d/lakefile.lean" ]; do
      d=$(dirname "$d")
    done
    [ "$d" = "." ] && [ ! -f lakefile.toml ] && [ ! -f lakefile.lean ] && echo "$f"
  done
}

if [ ${#targets[@]} -eq 0 ]; then mapfile -t targets < <(discover); fi
if [ $list -eq 1 ]; then printf '%s\n' "${targets[@]}"; exit 0; fi
[ ${#targets[@]} -gt 0 ] || { echo "no Lean targets found" >&2; exit 3; }
command -v lake > /dev/null || { echo "lake not on PATH (install elan)" >&2; exit 3; }
command -v python3 > /dev/null || { echo "python3 not on PATH (target path normalization)" >&2; exit 3; }

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
fail=0

run_target() {
  local t slug log status
  if ! t=$(python3 - "$root" "$1" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
target = (root / sys.argv[2]).resolve(strict=True)
if not target.is_relative_to(root):
    raise SystemExit("proof target escapes the repository")
print(target.relative_to(root).as_posix())
PY
  ); then
    echo "FAIL_target_path $1" >&2
    return 1
  fi
  slug=$(echo "$t" | tr '/.' '__')
  log="$scratch/$slug"
  mkdir -p "$log"
  status=PASS
  if [ "$t" = "$archived_failed" ]; then
    local actual_sha256 pinned rc errors
    actual_sha256=$(sha256sum "$root/$t" 2>/dev/null | cut -d ' ' -f 1)
    if [ "$actual_sha256" != "$archived_failed_sha256" ]; then
      status=FAIL_archive_digest
      printf 'expected sha256 %s\nactual sha256   %s\n' \
        "$archived_failed_sha256" "$actual_sha256" > "$log/build.log"
    else
      pinned=$(cat "$root/tools/lean/lean-toolchain" 2>/dev/null || true)
      if [ -z "$pinned" ] || ! command -v timeout >/dev/null; then
        status=INFRA_archive_toolchain
        echo 'pinned Lean toolchain or timeout unavailable' > "$log/build.log"
      else
        (cd "$(dirname "$root/$t")" && ELAN_TOOLCHAIN="$pinned" timeout 180 \
          lean -o "$log/negative.olean" "$root/$t") > "$log/build.log" 2>&1
        rc=$?
        errors=$(grep -c ' error(' "$log/build.log" || true)
        if [ "$rc" -eq 124 ]; then
          status=INFRA_archive_timeout
        elif [ "$rc" -ne 1 ] || [ "$errors" -ne 1 ] || \
          ! grep -Fq "$archived_failed_error" "$log/build.log"; then
          status=FAIL_archive_diagnostic
        else
          status=PASS_expected_failure
        fi
      fi
    fi
    echo "$status" > "$log/status"
    if [ -n "$out" ]; then
      mkdir -p "$out/$slug"
      cp "$log/build.log" "$log/status" "$out/$slug/"
    fi
    printf '%-22s %4s thm %3s trusted  %s\n' "$status" 0 0 "$t"
    if [ "$status" = PASS_expected_failure ]; then return 0; fi
    head -5 "$log/build.log" | sed 's/^/    /'
    case "$status" in INFRA_*) return 3 ;; *) return 1 ;; esac
  fi
  if [ -d "$root/$t" ]; then
    # Lake project. Mathlib projects fetch Mathlib's prebuilt cache first; a
    # failed fetch is an infrastructure error, never evidence about a proof.
    if grep -q '"name": *"mathlib"' "$root/$t/lake-manifest.json" 2>/dev/null; then
      if ! (cd "$root/$t" && lake exe cache get) > "$log/cache.log" 2>&1; then
        echo INFRA_cache > "$log/status"
        if [ -n "$out" ]; then
          mkdir -p "$out/$slug"
          cp "$log/cache.log" "$log/status" "$out/$slug/"
        fi
        echo "INFRA_cache   $t (lake exe cache get failed)"
        return 3
      fi
    fi
    if ! (cd "$root/$t" && lake build) > "$log/build.log" 2>&1; then
      status=FAIL_build
    else
      local f module source_rel target private_dir attempt lake_path
      local -a sources=() source_paths=() mods=()
      private_dir="$log/private-olean"
      mkdir -p "$private_dir"
      : > "$log/source-build.log"
      # A default target may omit an entire tracked module. Build each
      # registered source explicitly; compile an unregistered source in a
      # private directory so it still reaches the same axiom audit.
      while IFS= read -r -d '' f; do
        case "$f" in
          *.lean) ;;
          *) continue ;;
        esac
        module=$f
        [ "$t" = . ] || module=${f#"$t"/}
        case "$module" in
          lakefile.lean|AxiomAudit.lean|*/AxiomAudit.lean) continue ;;
        esac
        source_rel=${module%.lean}
        # Quote path components as Lean identifiers: a tracked directory can
        # contain a hyphen, which Lake otherwise parses as target syntax.
        module=${source_rel//\//».«}
        sources+=("+«$module»")
        source_paths+=("$source_rel")
        mods+=("«$module»")
      done < <(cd "$root" && git ls-files -z -- "$t")
      if [ ${#sources[@]} -eq 0 ]; then
        status=FAIL_no_sources
      else
        if ! lake_path=$(cd "$root/$t" && lake env printenv LEAN_PATH); then
          echo 'could not read Lake LEAN_PATH' >> "$log/source-build.log"
          status=FAIL_source_build
        fi
        for ((i=0; i<${#sources[@]}; i++)); do
          [ "$status" = PASS ] || break
          source_rel=${source_paths[i]}
          module=${source_rel//\//.}
          attempt="$log/source-attempt.log"
          if (cd "$root/$t" && lake build "${sources[i]}") > "$attempt" 2>&1; then
            cat "$attempt" >> "$log/source-build.log"
          elif grep -Fq "unknown module \`$module\`" "$attempt"; then
            cat "$attempt" >> "$log/source-registration.log"
            target="$private_dir/$source_rel.olean"
            mkdir -p "$(dirname "$target")"
            if ! (cd "$root/$t" && LEAN_PATH="$private_dir:$lake_path" \
              lean -o "$target" "$source_rel.lean") >> "$log/source-build.log" 2>&1; then
              status=FAIL_source_build
              break
            fi
            printf 'privately compiled %s\n' "$source_rel.lean" >> "$log/source-build.log"
          else
            cat "$attempt" >> "$log/source-build.log"
            status=FAIL_source_build
            break
          fi
        done
        if [ "$status" = PASS ]; then
          # Audit exactly the tracked source modules. A previous local build
          # may have left stale .olean files that are not in this Git tree.
          if [ ${#mods[@]} -eq 0 ]; then
            status=FAIL_no_modules
          elif ! (cd "$root/$t" && LEAN_PATH="$private_dir:$lake_path" \
            lean --run "$audit" -- "${trust_args[@]}" "${mods[@]}") > "$log/audit.log" 2>&1; then
            status=FAIL_audit
          fi
        fi
      fi
    fi
  else
    # Standalone file: compile into a private olean directory, then audit it.
    local mod dir toolchain
    mod=$(basename "$t" .lean)
    dir="$log/olean"
    mkdir -p "$dir"
    toolchain=$(cat "$(dirname "$root/$t")/lean-toolchain" 2>/dev/null || true)
    if ! (cd "$(dirname "$root/$t")" && lean -o "$dir/$mod.olean" "$root/$t") > "$log/build.log" 2>&1; then
      status=FAIL_build
    elif ! (cd "$(dirname "$root/$t")" && LEAN_PATH="$dir:${LEAN_PATH:-}" \
      lean --run "$audit" -- "${trust_args[@]}" "$mod") > "$log/audit.log" 2>&1; then
      status=FAIL_audit
    fi
    [ -n "$toolchain" ] && echo "toolchain pin: $toolchain" >> "$log/build.log"
  fi
  # `sorry` that elaborated without being used by a theorem still warns at build time.
  if [ "$status" = PASS ] && grep -q "declaration uses 'sorry'" "$log/build.log" "$log/source-build.log" 2>/dev/null; then
    status=FAIL_sorry_warning
  fi
  echo "$status" > "$log/status"
  if [ -n "$out" ]; then mkdir -p "$out/$slug" && cp -r "$log"/*.log "$log/status" "$out/$slug/"; fi
  local n
  n=$(grep -o 'audited [0-9]* theorems' "$log/audit.log" 2>/dev/null | grep -o '[0-9]*' || echo 0)
  local tr
  tr=$(grep -o '[0-9]* trusted' "$log/audit.log" 2>/dev/null | grep -o '[0-9]*' || echo 0)
  printf '%-22s %4s thm %3s trusted  %s\n' "$status" "${n:-0}" "${tr:-0}" "$t"
  if [ "$status" != PASS ]; then
    grep -E '^FAIL|error|no theorems' "$log/audit.log" "$log/build.log" "$log/source-build.log" 2>/dev/null | head -5 | sed 's/^/    /'
    return 1
  fi
}

infra=0
for t in "${targets[@]}"; do
  run_target "$t"
  case $? in 0) ;; 3) infra=1 ;; *) fail=1 ;; esac
done
[ $fail -eq 1 ] && exit 1
[ $infra -eq 1 ] && exit 3
exit 0
