#!/usr/bin/env bash
# Use as a RunPod container start command. Environment selects the mesh/config.
set -euo pipefail
umask 077
if [[ -z ${WB_ROOT:-} ]]; then
  if [[ -d /runpod-volume ]]; then WB_ROOT=/runpod-volume/workmesh;
  elif [[ -d /workspace ]]; then WB_ROOT=/workspace/.workmesh;
  else WB_ROOT=${XDG_DATA_HOME:-$HOME/.local/share}/workmesh; fi
fi
export WB_ROOT
entry=${WORKMESH_SCRIPT:-}
if [[ -z $entry ]] && command -v workmesh >/dev/null 2>&1; then entry=$(command -v workmesh); fi
if [[ -z $entry ]]; then
  : "${BOOTSTRAP_URL:?Set an HTTPS URL for your hosted, preferably commit-pinned bootstrap.sh}"
  [[ $BOOTSTRAP_URL = https://* ]] || { echo 'BOOTSTRAP_URL must use HTTPS' >&2; exit 1; }
  mkdir -p "$WB_ROOT"
  staged=$(mktemp "$WB_ROOT/.bootstrap.XXXXXX")
  trap 'rm -f "$staged"' EXIT
  curl --fail --location --retry 3 --proto '=https' --proto-redir '=https' "$BOOTSTRAP_URL" -o "$staged"
  chmod 700 "$staged"
  mv "$staged" "$WB_ROOT/bootstrap.sh"
  trap - EXIT
  entry=$WB_ROOT/bootstrap.sh
fi
args=(run --root "$WB_ROOT" --no-login)
[[ -z ${WORKMESH_CONFIG:-} ]] || args+=(--config "$WORKMESH_CONFIG")
if [[ ! -f $WB_ROOT/env.sh || ${INSTALL_ON_START:-no} = yes ]]; then args+=(--install); fi
if [[ $# = 0 ]]; then set -- sleep infinity; fi
exec bash "$entry" "${args[@]}" -- "$@"
