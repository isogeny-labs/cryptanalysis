#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/bin:/bin

# Materialize Nsight Systems without mutating the digest-pinned base image.
# The exact .deb binds every packaged byte; dpkg-deb only extracts it into the
# caller-owned fresh task root. Missing base-image DSOs fail closed when the
# registered binary is probed instead of triggering package resolution.
readonly systems_package='nsight-systems-2026.3.2'
readonly systems_version='2026.3.2.476-263238834031v0'
readonly systems_deb_url='https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/nsight-systems-2026.3.2_2026.3.2.476-1_amd64.deb'
readonly systems_deb_sha256='e9bf0ff9c613ff5545095a4177676a9579cb666e78c8621c3792f3559e2c1690'
readonly systems_deb_bytes='448261416'
readonly systems_binary_relative='opt/nvidia/nsight-systems/2026.3.2/target-linux-x64/nsys'
readonly systems_binary_sha256='68a5fb843322bda1b090900a0297b9d5bee43daf8b870a809a6f8aa93059ae16'
readonly systems_binary_bytes='87282816'

destination=${1:?usage: extract_nsys_tools_v11.sh /tmp/cryptanalysis-gpu-geometry-v11.TOKEN/nsys-package}
[[ $destination =~ ^/tmp/cryptanalysis-gpu-geometry-v11\.[A-Za-z0-9_]+/nsys-package$ ]] || {
  echo 'Nsight extraction destination is outside the fresh v11 task root' >&2
  exit 2
}
[[ ! -e $destination && ! -L $destination ]] || {
  echo 'Nsight extraction destination already exists' >&2
  exit 2
}

for tool in /usr/bin/curl /usr/bin/dpkg-deb /usr/bin/id /usr/bin/mkdir \
            /usr/bin/mktemp /usr/bin/realpath /usr/bin/rm /usr/bin/sha256sum \
            /usr/bin/stat; do
  [[ -x $tool ]] || { echo "missing exact extraction tool: $tool" >&2; exit 2; }
done
parent=${destination%/*}
[[ -d $parent && ! -L $parent && $(/usr/bin/realpath -e -- "$parent") = "$parent" \
   && $(/usr/bin/stat -c %u "$parent") = "$(/usr/bin/id -u)" ]] || {
  echo 'Nsight extraction parent is not the caller-owned fresh task root' >&2
  exit 2
}

workdir=$(/usr/bin/mktemp -d -t misagi-nsight-extract.XXXXXXXX)
complete=0
cleanup() {
  /usr/bin/rm -rf -- "$workdir"
  if (( ! complete )); then
    /usr/bin/rm -rf -- "$destination"
  fi
}
trap cleanup EXIT

systems_deb="$workdir/nsight-systems.deb"
/usr/bin/curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error \
  --output "$systems_deb" "$systems_deb_url"
[[ $(/usr/bin/stat -c %s "$systems_deb") = "$systems_deb_bytes" ]] || {
  echo 'profile-tool package byte length mismatch' >&2
  exit 1
}
printf '%s  %s\n' "$systems_deb_sha256" "$systems_deb" \
  | /usr/bin/sha256sum --check --strict

[[ $(/usr/bin/dpkg-deb --field "$systems_deb" Package) = "$systems_package" ]] || {
  echo 'profile-tool package name mismatch' >&2
  exit 1
}
[[ $(/usr/bin/dpkg-deb --field "$systems_deb" Version) = "$systems_version" ]] || {
  echo 'profile-tool package version mismatch' >&2
  exit 1
}
[[ $(/usr/bin/dpkg-deb --field "$systems_deb" Architecture) = amd64 ]] || {
  echo 'profile-tool package architecture mismatch' >&2
  exit 1
}

/usr/bin/mkdir -- "$destination"
/usr/bin/dpkg-deb --extract "$systems_deb" "$destination"
binary="$destination/$systems_binary_relative"
[[ -x $binary ]] || { echo 'extracted profiler binary is absent' >&2; exit 1; }
[[ $(/usr/bin/stat -c %s "$binary") = "$systems_binary_bytes" ]] || {
  echo 'extracted profiler binary byte length mismatch' >&2
  exit 1
}
observed=$(/usr/bin/sha256sum "$binary")
[[ ${observed%% *} = "$systems_binary_sha256" ]] || {
  echo 'extracted profiler binary hash mismatch' >&2
  exit 1
}

complete=1
printf 'Extracted profiler package: %s=%s\n' "$systems_package" "$systems_version"
printf 'Extracted profiler binary: %s\n' "$binary"
