Run `census overlap-3-4` with the generator abscissae on standard input,
one decimal integer per line. It prints the number of finite points reachable
both by exactly three and by exactly four signed generators, allowing repeats.
The default census provides a control: add the exact-three and exact-four
counts and subtract the radius-four finite count.

The overlap mode stores distinct finite triple abscissae in a hash set.
A bit filter skips impossible matches while streaming quadruples. An exact
match erases its abscissa, so duplicate encounters count once. Doubling the
number erased counts both signs on this odd-order curve. SparseOverlap.lean
proves the erase-count identity for a stream with arbitrary repetitions.
