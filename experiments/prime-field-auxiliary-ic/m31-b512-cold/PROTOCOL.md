# M31 B512 cold basis-size validation

The pilot used the five already published public targets at seed 0 and found
B512 faster than B384 on three of five charged wall comparisons. This pilot
is exploratory. Freeze the validation below before running seeds 1 and 2 or
repeating seed 0. Do not tune the binary, base order, lane count or hash
filter during the validation.

Use p=2147483647, E:y²=x³+2x+14, n=2147505293, G=(1,814455902), and
the five Q in `m31-integrated-local-screen/fresh-public.json`, SHA256
`dc724fc613d9c2b824b90d59c876f1f7f84b3273d8d607c648e1ba3fbc089252`.
Use the existing release `m31-fast` binary, SHA256
`e5f13b960f620e6aaae3c99ca17ee82963b4df981d89585688b8bbe9a35b4804`.
Arms: interval B384 and interval B512, each with m=2, indexed signed pair
table, 64 lanes, 64 pair chunk, four million query and five-second online
caps. Add the archived C++ rho implementation compiled from the frozen
snapshot before timing as a same-target generic control. Fresh child process
per arm. Run five Q x seeds 0,1,2, shuffle block order with
`random.Random(2026112852)`, rotate arm order by `(target+seed) mod 3`.
Preserve failures, incomplete and timeout arms.

External wall starts before child launch and ends after output parsing and
independent public group-equation verification. CPU is parent plus child user
and system deltas around that scope. Save every stdout/stderr, hashes, phase
timings and counts. The primary selection gate is B512 over B384: at least
12/15 matched wins in each of wall and CPU and median paired B384/B512 ratio
at least 1.15 in both. A separate breakthrough gate requires B512 to beat
matched rho on both charged medians and at least 12/15 paired cases in wall
and CPU. If neither gate passes, retain the negative result. This is an
existing base-size choice, not a novel algorithm; no Lean theorem about
timestamp ratios is called for.
