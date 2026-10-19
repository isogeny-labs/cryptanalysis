# Native build attempts

The first compile invocation omitted the include directory for the
archived `rotated_terms.hpp` dependency and stopped at a missing-header
error. The second supplied that include directory but tried to import
`source_full.cpp` with a renamed `main`; the imported file resets that
macro and defines its own `main`, so the compiler stopped at a
redefinition. The final build copied only the archived source helpers
into `source_helpers.hpp`, then compiled both `full_stream.cpp` and
`full_stream_linear.cpp` with `-O3 -std=c++20 -DNDEBUG` and the pinned
include directory. Both binaries compiled successfully with the
archived field kernel's non-void return-path warning. The final source,
helper, field-kernel, and binary hashes are in `build_result.json` and
the frozen producer/query protocols. The two initial diagnostics were
compiler setup failures before any measured run.
