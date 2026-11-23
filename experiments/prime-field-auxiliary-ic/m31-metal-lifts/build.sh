#!/bin/bash
set -eo pipefail
cd "$(dirname "$0")"
{
  sed '/^int main(/,$d' ../m31-projection-label/bench.cpp
  sed '/^int main(/,$d' ../m31-balanced-square/census.inc
  sed '/^int main(/,$d' ../m31-balanced-square/fused.inc
  if [[ ${2:-} == emit ]]; then
    sed '/^int main(/,$d' panel.inc
    sed '/^int main(/,$d' storage.inc
    cat emit.inc
  elif [[ ${2:-} == storage ]]; then
    sed '/^int main(/,$d' panel.inc
    cat storage.inc
  else
    cat panel.inc
  fi
} | clang++ -x objective-c++ -O3 -std=c++17 -mcpu=native -fobjc-arc - -framework Foundation -framework Metal -o "${1:?output executable path required}"
