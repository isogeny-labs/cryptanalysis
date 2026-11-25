# Shared M31 ordinate computation for a reflected twist

At the signed-smooth coordinate x, evaluate the target cubic f(x)=x³+2x+14.
At the reflected coordinate -x, the twist cubic u³+2u-14 evaluates to -f(x).
The exponent 2²⁹ is even, so the candidate ordinate is identical at the two
inputs. Its square gives one of the two signs. The routine writes the canonical
ordinate or the field-prime sentinel independently to each output. Zero receives
a valid zero ordinate on both sides. Reflection.lean proves the field identities.

Run `sh replay.sh` to regenerate the two-array experiment. Both paths reuse
the cubic evaluation and emit both arrays. Separate performs both exponentiations.
Shared performs one. The Python oracle evaluates each cubic directly at its own
coordinate. The 392 signed-smooth roots produce 195 target and 197 reflected
twist points, with a disjoint split on this fixture. These arrays correspond to
two different curves. Upstream basis setup is the frozen sixteen-chain path.

Each scope has eight warmup pairs and 128 measured pairs, alternating order.
Prepacked times the FFI call with allocated buffers. Lift includes Python packing,
allocation and conversion. Setup additionally regenerates and checks the public
fiber and filters smooth coordinates. The paired median wall speedups for the
two recorded builds were 1.610×/1.615× prepacked, 1.042×/1.024× for lift,
and 1.005×/1.003× for complete dual setup. Two preliminary builds timed lift
and setup only and gave 1.035×/1.036× and 1.003×/1.003× respectively.
