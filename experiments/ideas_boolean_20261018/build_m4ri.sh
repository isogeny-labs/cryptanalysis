#!/usr/bin/env bash
set -euo pipefail
task_dir=$(cd -- "$(dirname -- "$0")" && pwd)
archive="$task_dir/sources/m4ri-20260122.tar.gz"
mkdir -p "$task_dir/sources" "$task_dir/toolchain"
if [[ ! -f "$archive" ]]; then
  curl -sSfL --max-time 60 https://github.com/malb/m4ri/releases/download/20260122/m4ri-20260122.tar.gz -o "$archive"
fi
printf '%s  %s\n' 7e033ca1fd36be8861e2f67d9d124c398fc0d830209bb0226462485876346404 "$archive" | sha256sum --check
if [[ ! -d "$task_dir/sources/m4ri-20260122" ]]; then
  tar -xzf "$archive" -C "$task_dir/sources"
fi
cd "$task_dir/sources/m4ri-20260122"
./configure --prefix="$task_dir/toolchain/m4ri" --disable-openmp --enable-static --disable-shared
make -j1
make install
make -C tests test_elimination
./tests/test_elimination
