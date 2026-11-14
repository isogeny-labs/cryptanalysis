#!/usr/bin/env bash
# Build pinned M4GB solver binaries (cr-marcstevens/m4gb, GPL-3) with this
# repository's patches applied, and write a manifest with every hash.
#
#   scripts/m4gb_build.sh [--prefix DIR] [--source DIR] [--no-patches] CONFIG...
#
# CONFIG is n<MAXVARS>_gf<FIELDSIZE>, e.g. n128_gf2 n20_gf31.  The default
# prefix is $PWD/.m4gb; binaries land in <prefix>/bin/solver_m4gb_<CONFIG> and
# <prefix>/MANIFEST.json records the upstream commit, the patch hashes, the
# compiler and the binary hashes.  M4GB stays a separate GPL-3 binary: the
# `ca m4gb` subcommand only ever runs it as a subprocess (tools/ca_cli.c).
set -euo pipefail

UPSTREAM_URL="https://github.com/cr-marcstevens/m4gb"
# 2026-09-25 "Faster Gebauer-Moller implementation" (includes PR #14, the
# Gebauer-Moeller F-criterion fix).
UPSTREAM_COMMIT="01860a52dacb111d6e1533bc7547b2dc8f034073"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/.." && pwd)"
patches_dir="$repo/third_party/m4gb-patches"
prefix="$PWD/.m4gb"
source_dir=""
apply_patches=1
configs=()
while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) prefix="$2"; shift 2 ;;
    --source) source_dir="$2"; shift 2 ;;
    --no-patches) apply_patches=0; shift ;;
    -h|--help) sed -n 2,12p "$0"; exit 0 ;;
    n*_gf*) configs+=("$1"); shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ ${#configs[@]} -gt 0 ] || { echo "no CONFIG given (e.g. n128_gf2)" >&2; exit 2; }

mkdir -p "$prefix/bin"
prefix="$(cd "$prefix" && pwd)"
[ -n "$source_dir" ] || source_dir="$prefix/src"

if [ ! -d "$source_dir/.git" ]; then
  git clone -q "$UPSTREAM_URL" "$source_dir"
fi
git -C "$source_dir" fetch -q origin "$UPSTREAM_COMMIT" 2>/dev/null || true
git -C "$source_dir" checkout -q --detach "$UPSTREAM_COMMIT"
git -C "$source_dir" reset -q --hard "$UPSTREAM_COMMIT"
git -C "$source_dir" clean -qfdx
actual="$(git -C "$source_dir" rev-parse HEAD)"
[ "$actual" = "$UPSTREAM_COMMIT" ] || { echo "upstream commit mismatch: $actual" >&2; exit 1; }

patch_list=()
if [ "$apply_patches" = 1 ]; then
  for p in "$patches_dir"/*.patch; do
    [ -e "$p" ] || continue
    git -C "$source_dir" apply --check "$p"
    git -C "$source_dir" apply "$p"
    patch_list+=("$p")
  done
fi

(
  cd "$source_dir"
  autoreconf --install >"$prefix/autoreconf.log" 2>&1
  ./configure >"$prefix/configure.log" 2>&1
  for cfg in "${configs[@]}"; do
    maxvars="${cfg#n}"; maxvars="${maxvars%%_gf*}"
    fieldsize="${cfg##*_gf}"
    make -j"$(nproc)" MAXVARS="$maxvars" FIELDSIZE="$fieldsize" m4gb >"$prefix/make-$cfg.log" 2>&1
    cp "bin/solver_m4gb_$cfg" "$prefix/bin/solver_m4gb_$cfg"
  done
)

sha() { sha256sum "$1" | cut -d' ' -f1; }
{
  echo "{"
  echo "  \"schema\": \"m4gb-build/v1\","
  echo "  \"upstream_url\": \"$UPSTREAM_URL\","
  echo "  \"upstream_commit\": \"$UPSTREAM_COMMIT\","
  echo "  \"built_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"compiler\": \"$(g++ --version | head -1)\","
  echo "  \"cxxflags\": \"$(grep -m1 -o 'g++ .*m4gb\.cpp' "$prefix/make-${configs[0]}.log" | tr ' ' '\n' | grep -E '^-(O|m|std|f|D(MAXVARS|FIELDSIZE))' | tr '\n' ' ' | sed 's/ $//')\","
  echo "  \"patches\": ["
  first=1
  for p in "${patch_list[@]}"; do
    [ $first = 1 ] || echo ","
    first=0
    printf '    {"file": "%s", "sha256": "%s"}' "$(basename "$p")" "$(sha "$p")"
  done
  echo
  echo "  ],"
  echo "  \"binaries\": ["
  first=1
  for cfg in "${configs[@]}"; do
    [ $first = 1 ] || echo ","
    first=0
    printf '    {"config": "%s", "path": "bin/solver_m4gb_%s", "sha256": "%s"}' "$cfg" "$cfg" "$(sha "$prefix/bin/solver_m4gb_$cfg")"
  done
  echo
  echo "  ]"
  echo "}"
} >"$prefix/MANIFEST.json"
echo "built ${configs[*]} into $prefix/bin; manifest $prefix/MANIFEST.json"
