#!/bin/sh
set -eu
cd "$(dirname "$0")"
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT HUP INT TERM
${CXX:-c++} -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror test.cpp -o "$build_dir/test"
"$build_dir/test"
