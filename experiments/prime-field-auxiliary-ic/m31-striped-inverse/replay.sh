#!/bin/sh
# Run from any working directory. CSV goes to stdout.
set -eu
cd "$(dirname "$0")/.."
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
cc -O3 -shared -fPIC m31-native-layer/layer.c m31-native-fiber/fiber.c -o "$d/control.so"
cc -O3 -fPIC -Dm31_translate=scalar_translate -c m31-native-layer/layer.c -o "$d/layer.o"
cc -O3 -fPIC -Dm31_reciprocals=scalar_reciprocals -c m31-native-fiber/fiber.c -o "$d/fiber.o"
cc -O3 -shared -fPIC m31-striped-inverse/stripes.c "$d/layer.o" "$d/fiber.o" -o "$d/stripes.so"
variant() {
    name=$1
    shift
    cc -O3 -shared -fPIC "$@" m31-striped-inverse/stripes.c "$d/layer.o" "$d/fiber.o" -o "$d/$name.so"
}
case "${1:-phase}" in
    anchor) variant width16 -DM31_LANES=16 ;;
    factorial)
        variant one-rem -DM31_LANES=1 -DM31_USE_REMAINDER
        variant one-fold -DM31_LANES=1
        variant four-rem -DM31_USE_REMAINDER
        ;;
    width)
        for lanes in 8 16 32; do variant "width$lanes" "-DM31_LANES=$lanes"; done
        ;;
    phase) set -- ;;
    *) exit 2 ;;
esac
cc -O3 -flto -mcpu=native -shared -fPIC m31-native-product/archived-lifts/lift.c m31-native-product/product.c -o "$d/lift.so"
cc -O3 -shared -fPIC m31-packed-fiber/distinct.c -o "$d/distinct.so"
c++ -O3 -std=c++17 -shared -fPIC m31-batch-smooth/independent.cpp -o "$d/filter.so"
if [ "${1:-}" = anchor ]; then
    uv run --isolated --with sympy --python 3.13 python m31-packed-fiber/distinct_replay.py "$d/lift.so" "$d/width16.so" "$d/width16.so" "$d/filter.so" "$d/distinct.so" --anchor
    exit
fi
uv run --isolated --with sympy --python 3.13 python m31-striped-inverse/compare.py "$d/lift.so" "$d/control.so" "$d/control.so" "$d/filter.so" "$d/distinct.so" "$@"
