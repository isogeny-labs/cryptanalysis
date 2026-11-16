#!/usr/bin/env bash
# Thin, local-only entry point for the pinned OpenResearch release.
set -euo pipefail

readonly ORX_VERSION='0.2.27'
readonly INSTALLER_SHA256='fbf1c9a92f525d2cb0bf902016d22fdc5dd9a275f781b554a32e3c2c8d2f6eb6'
readonly INSTALLER_URL="https://github.com/alphaXiv/OpenResearch/releases/download/v${ORX_VERSION}/openresearch-cli-installer.sh"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
prefix="${OPENRESEARCH_PREFIX:-${HOME}/.local}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/openresearch.sh <setup|doctor|up|skill> [arguments...]

  setup   Install the pinned CLI if absent; disable anonymous telemetry.
  doctor  Check the CLI and repository skill without network access.
  up      Open the loopback dashboard; add this checkout as an existing project.
  skill   Print the bundled CLI guide (optional module name).

Other commands are passed to orx from this repository's root.
OPENRESEARCH_PREFIX selects the installation prefix (default: ~/.local).
OPENRESEARCH_BIN selects an existing executable explicitly.
USAGE
}

resolve_orx() {
  if [[ -n "${OPENRESEARCH_BIN:-}" ]]; then
    orx_bin="$OPENRESEARCH_BIN"
  elif [[ -x "$prefix/bin/orx" ]]; then
    orx_bin="$prefix/bin/orx"
  else
    orx_bin="$(command -v orx || true)"
  fi
  [[ -n "$orx_bin" && -x "$orx_bin" ]]
}

require_orx() {
  if ! resolve_orx; then
    echo 'OpenResearch is missing. Run: bash scripts/openresearch.sh setup' >&2
    exit 1
  fi
}

setup() {
  if ! resolve_orx; then
    if [[ -n "${OPENRESEARCH_BIN:-}" ]]; then
      echo 'OPENRESEARCH_BIN must name an executable; refusing another install.' >&2
      exit 1
    fi
    command -v curl >/dev/null
    installer_dir="$(mktemp -d)"
    trap 'rm -rf -- "$installer_dir"' EXIT
    curl --fail --silent --show-error --location --connect-timeout 20 \
      --max-time 180 "$INSTALLER_URL" -o "$installer_dir/install.sh"
    if command -v sha256sum >/dev/null; then
      actual_sha="$(sha256sum "$installer_dir/install.sh")"
    elif command -v shasum >/dev/null; then
      actual_sha="$(shasum -a 256 "$installer_dir/install.sh")"
    else
      echo 'Install sha256sum or shasum before running setup.' >&2
      exit 1
    fi
    if [[ "${actual_sha%% *}" != "$INSTALLER_SHA256" ]]; then
      echo 'OpenResearch installer checksum mismatch; nothing executed.' >&2
      exit 1
    fi
    OPENRESEARCH_CLI_INSTALL_DIR="$prefix" OPENRESEARCH_CLI_NO_MODIFY_PATH=1 \
      sh "$installer_dir/install.sh"
    orx_bin="$prefix/bin/orx"
  fi
  installed_version="$("$orx_bin" --version)"
  if [[ "$installed_version" != "orx $ORX_VERSION" ]]; then
    echo "Expected orx $ORX_VERSION; found $installed_version. Existing CLI left in place." >&2
    exit 1
  fi
  "$orx_bin" telemetry off
  echo "OpenResearch $ORX_VERSION ready; repository skill: .agents/skills/orx/SKILL.md"
}

cd -- "$repo_root"
command_name="${1:-help}"
if [[ $# -gt 0 ]]; then shift; fi
case "$command_name" in
  help|-h|--help) usage ;;
  setup) setup ;;
  doctor)
    require_orx
    "$orx_bin" --version
    test -r .agents/skills/orx/SKILL.md
    test -r .claude/skills/orx/SKILL.md
    "$orx_bin" telemetry status
    printf 'Repository: %s\nDashboard: http://127.0.0.1:4791\n' "$repo_root"
    ;;
  up)
    require_orx
    exec "$orx_bin" up "$@"
    ;;
  *)
    require_orx
    exec "$orx_bin" "$command_name" "$@"
    ;;
esac
