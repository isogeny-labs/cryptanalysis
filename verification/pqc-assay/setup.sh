#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=toolchain.env
source "$here/toolchain.env"
cache=${ASSAY_CACHE:-"$here/.cache"}
mkdir -p "$cache"
case "$(uname -s)/$(uname -m)" in
    Linux/x86_64) ;;
    *) echo 'This bootstrap supports Linux x86_64.' >&2; exit 2 ;;
esac
saw_home=${ASSAY_SAW_HOME:-"$cache/saw-$ASSAY_SAW_VERSION"}
if [[ ! -x "$saw_home/bin/saw" ]]; then
    archive="$cache/$ASSAY_SAW_ASSET"
    curl --fail --location --retry 3 --output "$archive.partial" \
        "https://github.com/GaloisInc/saw-script/releases/download/v$ASSAY_SAW_VERSION/$ASSAY_SAW_ASSET"
    printf '%s  %s\n' "$ASSAY_SAW_SHA256" "$archive.partial" | sha256sum --check -
    mv "$archive.partial" "$archive"
    mkdir -p "$saw_home"
    tar -xzf "$archive" -C "$saw_home" --strip-components=1
fi
"$saw_home/bin/saw" --version 2>&1 | grep -F "$ASSAY_SAW_VERSION ("
