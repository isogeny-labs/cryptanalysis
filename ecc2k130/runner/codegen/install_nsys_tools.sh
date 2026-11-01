#!/bin/bash
set -euo pipefail

# Runpod's minimal Ubuntu image does not configure NVIDIA's CUDA repository.
# Install its signed repository keyring from a content-pinned artifact, then
# request exact profiler package versions instead of whatever happens to be
# newest when a pod starts.
readonly keyring_url='https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb'
readonly keyring_sha256='d2a6b11c096396d868758b86dab1823b25e14d70333f1dfa74da5ddaf6a06dba'
readonly systems_package='nsight-systems-2026.3.2'
readonly systems_version='2026.3.2.476-263238834031v0'

if [[ $(id -u) -ne 0 ]]; then
  echo 'profile-tool install requires root' >&2
  exit 1
fi
if [[ $(dpkg --print-architecture) != amd64 ]]; then
  echo 'profile-tool install supports only Ubuntu amd64' >&2
  exit 1
fi

workdir=$(mktemp -d -t misagi-nsight-install.XXXXXXXX)
cleanup() {
  rm -rf -- "$workdir"
}
trap cleanup EXIT

keyring="$workdir/cuda-keyring.deb"
curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error \
  --output "$keyring" "$keyring_url"
printf '%s  %s\n' "$keyring_sha256" "$keyring" | sha256sum --check --strict
dpkg --install "$keyring"
apt-get update

for specification in "$systems_package=$systems_version"; do
  if ! apt-cache show "$specification" >/dev/null 2>&1; then
    echo "required profiler package unavailable: $specification" >&2
    apt-cache policy "${specification%%=*}" >&2 || true
    exit 1
  fi
done

DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  build-essential python3 \
  "$systems_package=$systems_version"

printf 'Selected profiler package: %s=%s\n' \
  "$systems_package" "$systems_version"
dpkg-query --show --showformat='Installed profiler package: ${Package}=${Version}\n' \
  "$systems_package"
