# Batch smoothness filter at M31

The local arm64 experiment compared the scalar filter with batches of 4, 8 and 16
on the 32,768 public depth-15 roots. Each of the 24 possible execution orders
appeared twice. In paired.csv, columns are wall nanoseconds per filter call.
The 16-coordinate prototype retained all 392 signed-211-smooth coordinates in
reference order. setup.csv records 64 alternating pairs of complete public
basis preparations after four warmups. The two paths differed only in the
filter library. Each call returned the same 195 ordered points.

Build the measured source with
`c++ -O3 -std=c++17 -shared -fPIC b16.cpp -o /tmp/m31-batch.so`.
Supply the resulting library as the filter argument to the neighboring
m31-packed-fiber replay. Inputs are canonical unsigned field coordinates.
The theorem in Batch.lean establishes the loop-order transformation and stable
selection for a lane-local update. The correspondence between compiled mask
operations and that update is tested empirically.
