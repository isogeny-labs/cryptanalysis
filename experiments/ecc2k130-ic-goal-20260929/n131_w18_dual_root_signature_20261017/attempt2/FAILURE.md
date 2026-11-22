# Frozen parser preflight conflated code and source mask

The second frozen census stopped while reading the archived row with selector code 138 and canonical source masks `(266,478)`. The source-mask XOR is 212 as required, but the 17-bit selector code is an encoding of the canonical mask and is not always numerically equal to `mask_a`. The corrected parser keeps the code as the algebraic input and checks the two exported masks against the frozen seed. This failure occurred before the dual-space or degree screen; the original source, protocol, stdout, and stderr remain here.
