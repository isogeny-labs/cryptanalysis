# Constant-reduction native preparation

One CUDA/L4 allocation,4CPU/8GiB900s, apt time; CPU arithmetic only. Build exact
published source default release, locked dependency graph,2compile jobs,780sbuild
cap, existing300sdebug compile/test aggregate inside allocation hard900s. No Rust
or dependency edits during compilation. No host retry or cap extension. Preserve
all exits/caps/logs, compiler/source/binary hashes, environment and host receipts.

Correctness only:15archive/loader controls,150complete maps (5fields x5chunks
x6implementations), existing4walker and2full-point tests, newconstant-reduction
unit and512state complete stream smoke for each field. Dynamic product/packed/
constant paths compare exact full maps with original scalar first witnesses.
Positive executed constant-pair counts mandatory in all5fields. Specialization
uses ordinary PCLMUL even on wide hosts; report counters for each path accurately.
Existing Python arithmetic checks2560exported states after fetch. No performance
conclusion from this allocation; freeze a successor protocol/inputs before timing.
