#!/usr/bin/env bash
# Qualification requires an actual CUDA/Metal worker; emulation is excluded.
set -euo pipefail
case "${CERTICOM_TEST_BACKEND:-}" in
    cuda|metal) ;;
    *) echo 'Set CERTICOM_TEST_BACKEND=cuda or metal for hardware qualification' >&2; exit 2 ;;
esac
certicom_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$certicom_root"
if [[ "$CERTICOM_TEST_BACKEND" == cuda ]]; then
    # nvcc selects the architecture of the GPU being qualified on this host.
    make -B -C gpu/certicom cuda ARCH="${CERTICOM_CUDA_ARCH:-native}"
else
    make -B -C gpu/certicom metal
fi
export CERTICOM_TEST_WORKER="$certicom_root/gpu/certicom/certicom_$CERTICOM_TEST_BACKEND"
"$CERTICOM_TEST_WORKER" --probe 2>&1 | tee certicom-device-probe.log
{
    git rev-parse HEAD
    uname -srm
    rustc -Vv
    cargo --version
    if [[ "$CERTICOM_TEST_BACKEND" == cuda ]]; then
        nvcc --version
        nvidia-smi --query-gpu=name,driver_version,pci.bus_id --format=csv
    else
        sw_vers
        xcrun clang++ --version
        system_profiler SPDisplaysDataType | sed -n '/Chipset Model:/p; /Vendor:/p; /Metal Support:/p'
    fi
    if command -v sha256sum >/dev/null; then digest=(sha256sum); else digest=(shasum -a 256); fi
    "${digest[@]}" "$CERTICOM_TEST_WORKER" gpu/certicom/arithmetic.h gpu/certicom/wire.hpp
    if [[ "$CERTICOM_TEST_BACKEND" == metal ]]; then "${digest[@]}" gpu/certicom/certicom.metallib; fi
} 2>&1 | tee certicom-device-identity.log
certicom_manifest=Cargo.toml
if [[ -f suite/Cargo.toml ]]; then certicom_manifest=suite/Cargo.toml; fi
cargo test --manifest-path "$certicom_manifest" --release --lib \
    certicom_dlp::device_tests -- --test-threads=1 --nocapture \
    2>&1 | tee certicom-device-tests.log
bash gpu/certicom/test-cli.sh 2>&1 | tee certicom-device-cli-tests.log
