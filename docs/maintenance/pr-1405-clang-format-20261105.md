# PR1405 formatting follow-up

## What was done

Applied the exact one-line diff emitted by the CI-pinned clang-format21.1.6 to the suffix-product loop in src/group_ec.c. Its changed-lines check then reports no modifications. The native release CMake build and all19 CTest entries completed successfully after restoring tracked sparse-checkout headers and usecase fixtures. [pcc:unverified]

## Decisions made

Keep the interleaved inversion algorithm and all recorded measurements unchanged. This is whitespace-only source maintenance; it adds no timing result. Sources checked: actual failing job127079533026, .clang-format, ec_batch_op, existing group tests and the project CMake/Makefile.

## Open threads

Fresh current-head CI/review and guarded merge.

## Errors

CMake was initially absent and was supplied through its standard tool package. Initial sparse builds lacked cuda/ca_device.cuh, hot64_selected.h and usecases/ecc2k130/tests; restored their exact tracked paths before the complete19-test pass. Original failed setup logs remain in the session workspace. [pcc:unverified]
