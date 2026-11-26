# Frozen same-target native rho reference

This protocol fixes a same-curve, same-generator, same-target generic rho
reference for the corrected network panel before running it. It uses the
repository's native C `ca solve --alg rho` implementation. Local results
have producer-only standing `[pcc:unverified]`.

## Instance and binary

- Curve: `y^2=x^3-3*x+7` over `GF(10007)`; pass `a=10004`, `b=7`, and
  subgroup order `10193` to the CLI.
- Generator: `(4634,6322)` from the frozen Sage fixture.
- Target: `(9780,4658) = 7001*G` from `cold_network_v2.json`.
- Build the CLI from this PR's C source in a separate local CMake Release
  build with `CA_BUILD_SHARED=OFF`, `CA_BUILD_STATIC=ON`, `CA_BUILD_TOOLS=ON`,
  `CA_BUILD_TESTS=OFF`, `CA_CUDA=OFF`, and no architecture override or LTO.
  Record compiler, host, source commit and binary SHA-256.

## Run and acceptance

Run 16 independent fixed seeds `1,...,16`. Each command uses `ca solve
--alg rho --group ec --p 10007 --a 10004 --b 7 --order 10193 --g
4634,6322 --h 9780,4658 --threads 1 --seed S --max-ops 1000000` with
the repository default negation map and other default rho tuning. Retain
exact command arguments, raw stdout/stderr, exit code, process wall and
child CPU time, reported group operations and iterations, and all failed or
censored seeds. Verify each returned scalar by multiplication on the same
curve, including the expected value 7001. Summarize median/range group
operations and the total wall/CPU across all 16 runs. Do not turn a short
single-run timing into a speed ratio.

This reference and the network native-scan wall/CPU include process launch,
but charge different work: rho performs full group search, while the network
solver totals omit isogeny maps, scalar generation, and sparse linear
algebra. Report that limit beside any comparison. `[pcc:unverified]`
