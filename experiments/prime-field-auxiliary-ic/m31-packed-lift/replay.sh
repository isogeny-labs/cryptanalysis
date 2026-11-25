#!/bin/sh
# Run from any working directory. CSV goes to stdout.
set -eu
cd "$(dirname "$0")/.."
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
cc -O3 -shared -fPIC m31-native-layer/layer.c m31-native-fiber/fiber.c -o "$d/control.so"
cc -O3 -fPIC -Dm31_translate=scalar_translate -c m31-native-layer/layer.c -o "$d/layer.o"
cc -O3 -fPIC -Dm31_reciprocals=scalar_reciprocals -c m31-native-fiber/fiber.c -o "$d/fiber.o"
cc -O3 -shared -fPIC -DM31_LANES=16 m31-striped-inverse/stripes.c "$d/layer.o" "$d/fiber.o" -o "$d/width16.so"
cc -O3 -flto -mcpu=native -shared -fPIC m31-packed-lift/compact.c m31-native-product/archived-lifts/lift.c m31-native-product/product.c -o "$d/lift.so"
cc -O3 -shared -fPIC m31-packed-fiber/distinct.c -o "$d/distinct.so"
c++ -O3 -std=c++17 -shared -fPIC m31-batch-smooth/independent.cpp -o "$d/filter.so"
uv run --isolated --with sympy --python 3.13 python m31-packed-lift/panel.py "$d/lift.so" "$d/width16.so" "$d/width16.so" "$d/filter.so" "$d/distinct.so"
