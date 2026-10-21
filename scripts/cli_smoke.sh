#!/usr/bin/env bash
#
# Exercise every `ca` subcommand and check the answers that are known in
# closed form.
#
# The point is coverage, not speed: if a public header gains a function that no
# command reaches, this script is where that shows up. Every command in
# `ca`'s usage text must appear here, and the assertions are chosen so a wrong
# answer fails rather than merely a crash.
#
# Usage: scripts/cli_smoke.sh [path-to-ca]   (default: build/ca)
set -euo pipefail

CA=${1:-build/ca}
if [ ! -x "$CA" ]; then
  echo "no ca binary at $CA — build it first (cmake --build build --target ca)" >&2
  exit 2
fi

fail=0
checks=0

# Assert that running `ca $*` succeeds and its output contains a string. The
# expected string is the first argument.
want() {
  local expect=$1
  shift
  checks=$((checks + 1))
  local out
  if ! out=$("$CA" "$@" 2>&1); then
    printf 'FAIL (exit) %s\n  %s\n' "$*" "$out" >&2
    fail=$((fail + 1))
    return
  fi
  case $out in
  *"$expect"*) : ;;
  *)
    printf 'FAIL %s\n  wanted: %s\n  got:    %s\n' "$*" "$expect" "$out" >&2
    fail=$((fail + 1))
    ;;
  esac
}

# Assert that `ca $*` reports "no such object" — exit status 1 with the given
# string in its output. The CLI distinguishes three outcomes: 0 for an answer,
# 1 for a well-posed question whose answer is "there is none" (not invertible,
# not a square, not on the curve), and 2 for a malformed invocation.
want_no() {
  local expect=$1
  shift
  checks=$((checks + 1))
  local out rc=0
  out=$("$CA" "$@" 2>&1) || rc=$?
  if [ "$rc" -ne 1 ]; then
    printf 'FAIL (wanted exit 1, got %d) %s\n  %s\n' "$rc" "$*" "$out" >&2
    fail=$((fail + 1))
    return
  fi
  case $out in
  *"$expect"*) : ;;
  *)
    printf 'FAIL %s\n  wanted: %s\n  got:    %s\n' "$*" "$expect" "$out" >&2
    fail=$((fail + 1))
    ;;
  esac
}

# Assert that `ca $*` exits non-zero. Used for the refusals that matter.
want_fail() {
  checks=$((checks + 1))
  if "$CA" "$@" >/dev/null 2>&1; then
    printf 'FAIL (expected non-zero exit) %s\n' "$*" >&2
    fail=$((fail + 1))
  fi
}

# Malformed options must fail before any solver work starts.
want_bad() {
  local expect=$1
  shift
  checks=$((checks + 1))
  local out rc=0
  out=$("$CA" "$@" 2>&1) || rc=$?
  if [ "$rc" -ne 2 ] || [[ "$out" != *"$expect"* ]]; then
    printf 'FAIL (wanted exit 2 and %s, got %d) %s\n  %s\n' "$expect" "$rc" "$*" "$out" >&2
    fail=$((fail + 1))
  fi
}

# ── information ─────────────────────────────────────────────────────────────
want '"version"' version
want '"cuda_compiled"' gpu-info

# ── number theory (ca_modarith.h) ───────────────────────────────────────────
# 3^100 mod 1000003, cross-checked against Python: 189751.
want '"result":"189751"' num powmod --base 3 --exp 100 --mod 1000003
# 2 is invertible mod 1000003 and 2 * 500002 = 1000004 = 1 (mod 1000003).
want '"result":"500002"' num invmod --a 2 --mod 1000003
# 6 is not invertible mod 9: gcd is 3.
want_no '"invertible":false' num invmod --a 6 --mod 9
want '"result":"6"' num gcd --a 24 --b 42
want '"result":"1000","exact":true' num isqrt --n 1000000
want '"exact":false' num isqrt --n 1000001
want '"result":"100"' num iroot --n 1000000 --k 3
# 4 is a square mod 1000003; its roots are +/-2, and -2 = 1000001.
want '"square":true' num sqrtmod --a 4 --p 1000003
want '"result":-1' num legendre --a 5 --p 1000003
want '"result":1' num legendre --a 4 --p 1000003
# x = 2 mod 3, x = 3 mod 5  =>  x = 8 mod 15.
want '"result":"8","modulus":"15"' num crt --r1 2 --m1 3 --r2 3 --m2 5
want_fail num crt --r1 1 --m1 4 --r2 1 --m2 6   # moduli not coprime
want '"result":"1000003"' num next-prime --n 1000000
# 1000003 is prime, so a primitive root has order p-1.
want '"order":"1000002"' num primitive-root --p 1000003
# pi(1000) = 168, first prime 2, last 997.
want '"count":168' num sieve --bound 1000
want '"last":997' num sieve --bound 1000
# The Montgomery domain must agree with schoolbook arithmetic on every op.
want '"agree":true' num mont --p 1000003 --a 12345 --b 67890
want '"agree":true' num mont --p 2147483647 --a 123456789 --b 987654321
want_fail num mont --p 1000004                   # even modulus
want_fail num mont --p 1                          # below the Montgomery floor
want_fail num mont --p 0                          # would divide by zero
want_fail num powmod --base 3 --exp 4 --mod 1     # degenerate modulus
# m1 * m2 must not wrap: the result is reduced against it, so a wrapped modulus
# would be printed alongside an answer not taken modulo it.
want_fail num crt --r1 1 --m1 18446744073709551557 --r2 1 --m2 3
want_fail num sieve --bound 99999999999           # would be an absurd allocation
want_fail num nonsense

# ── factorisation and primality ─────────────────────────────────────────────
want '"is_prime":true' prime 1000003
want '"is_prime":false' prime 1000001
# 2^32 - 1 = 3 * 5 * 17 * 257 * 65537.
want '65537' factor 4294967295
want_bad 'factor needs a positive uint64 N' factor -1
want '[factor] complete' factor 97 --verbose
want '"factors":[]' factor 1 --verbose
factor_tmp=$(mktemp -d)
FACTOR=(factor 1000036000099 --state-dir "$factor_tmp/local" \
  --progress-every 1 --checkpoint-every 1)
want_no '"status":"limit reached"' "${FACTOR[@]}" --max-steps 3
checks=$((checks + 1))
if [ ! -s "$factor_tmp/local/factor.ckpt" ] || \
   ! grep -q '"phase":"rho"' "$factor_tmp/local/factor.ckpt.progress.json"; then
  printf 'FAIL: factor partial checkpoint or phase progress missing\n' >&2
  fail=$((fail + 1))
fi
want '"factors":[[1000003,1],[1000033,1]]' "${FACTOR[@]}" --max-steps 1000000 --resume
checks=$((checks + 1))
if ! grep -q '"phase":"complete"' "$factor_tmp/local/factor.ckpt.progress.json" || \
   ! grep -q '"factors":\[\[1000003,1\],\[1000033,1\]\]' "$factor_tmp/local/result.json"; then
  printf 'FAIL: factor resume did not finish and persist the result\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' factor 1000036000100 \
  --state-dir "$factor_tmp/local" --resume
mkdir "$factor_tmp/bin" "$factor_tmp/remote"
cat >"$factor_tmp/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
src=$3 dst=$4
if [[ $src == s3://* ]]; then src=$CA_TEST_S3_ROOT; fi
if [[ $dst == s3://* ]]; then dst=$CA_TEST_S3_ROOT; fi
mkdir -p "$dst"
if compgen -G "$src/*" >/dev/null; then cp "$src/"* "$dst/"; fi
AWS
chmod +x "$factor_tmp/bin/aws"
FACTOR_S3=(factor 1000036000099 --state-dir "$factor_tmp/s3-local" \
  --s3-uri s3://test/factor --sync-every 1)
PATH="$factor_tmp/bin:$PATH" CA_TEST_S3_ROOT="$factor_tmp/remote" \
  want_no '"status":"limit reached"' "${FACTOR_S3[@]}" --max-steps 3
rm -rf "$factor_tmp/s3-local"
PATH="$factor_tmp/bin:$PATH" CA_TEST_S3_ROOT="$factor_tmp/remote" \
  want '"factors":[[1000003,1],[1000033,1]]' "${FACTOR_S3[@]}" \
  --max-steps 1000000 --resume
checks=$((checks + 1))
if [ ! -s "$factor_tmp/remote/factor.ckpt" ] || \
   ! grep -q '"phase":"complete"' "$factor_tmp/remote/factor.ckpt.progress.json"; then
  printf 'FAIL: factor S3 mirror or restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$factor_tmp/remote/factor.ckpt" "$factor_tmp/remote-good.ckpt"
printf X >>"$factor_tmp/s3-local/factor.ckpt"
PATH="$factor_tmp/bin:$PATH" CA_TEST_S3_ROOT="$factor_tmp/remote" \
  want_bad 'factor checkpoint failed validation before S3 sync' \
  "${FACTOR_S3[@]}" --resume
checks=$((checks + 1))
if ! cmp -s "$factor_tmp/remote/factor.ckpt" "$factor_tmp/remote-good.ckpt"; then
  printf 'FAIL: invalid local factor checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$factor_tmp"

# ── groups (ca_group.h) ─────────────────────────────────────────────────────
ZP=(--group zp --p 1000003 --order 1000002)
want '"order":"1000002"' group generator "${ZP[@]}"
# 2^100 mod 1000003 = 253109, so the group's scalar multiple must agree with
# `num powmod` — the same computation through two different abstractions.
want '"result":"253109"' group exp "${ZP[@]}" --elem 2 --k 100
want '"result":"253109"' num powmod --base 2 --exp 100 --mod 1000003
want '"result":"2"' group div "${ZP[@]}" --a 6 --b 3
want '"divides_group_order":true' group order "${ZP[@]}" --elem 2
want '"exponent"' group random "${ZP[@]}" --seed 7

EC=(--group ec --p 1000003 --a 2 --b 3)
want '"order":999708' ec-order --p 1000003 --a 2 --b 3
want '[ec-order] complete' ec-order --p 1000003 --a 2 --b 3 --verbose
ec_order_tmp=$(mktemp -d)
EC_ORDER=(ec-order --p 97 --a 2 --b 3 --state-dir "$ec_order_tmp/local" \
  --progress-every 1 --checkpoint-every 1)
want_no '"status":"limit reached"' "${EC_ORDER[@]}" --max-work 20
checks=$((checks + 1))
if [ ! -s "$ec_order_tmp/local/ec-order.ckpt" ] || \
   ! grep -q '"field_x":20' "$ec_order_tmp/local/ec-order.ckpt.progress.json"; then
  printf 'FAIL: ec-order scan checkpoint or progress missing\n' >&2
  fail=$((fail + 1))
fi
want '"order":100' "${EC_ORDER[@]}" --max-work 200 --resume
checks=$((checks + 1))
if [ ! -s "$ec_order_tmp/local/order-factor.ckpt" ] || \
   ! grep -q '"count_phase":"complete"' "$ec_order_tmp/local/result.json"; then
  printf 'FAIL: ec-order resume or factor artifact missing\n' >&2
  fail=$((fail + 1))
fi
EC_ORDER_FACTOR=(ec-order --p 1000003 --a 2 --b 3 \
  --state-dir "$ec_order_tmp/factor-local")
want_no '"status":"limit reached"' "${EC_ORDER_FACTOR[@]}" --max-factor-steps 3
checks=$((checks + 1))
if [ ! -s "$ec_order_tmp/factor-local/ec-order.ckpt" ] || \
   [ ! -s "$ec_order_tmp/factor-local/order-factor.ckpt" ]; then
  printf 'FAIL: ec-order count or factor checkpoint missing after factor cap\n' >&2
  fail=$((fail + 1))
fi
want '"order":999708' "${EC_ORDER_FACTOR[@]}" --resume
want_bad 'run manifest does not match' ec-order --p 97 --a 2 --b 4 \
  --state-dir "$ec_order_tmp/local" --resume
mkdir "$ec_order_tmp/bin" "$ec_order_tmp/remote"
cat >"$ec_order_tmp/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
src=$3 dst=$4
if [[ $src == s3://* ]]; then src=$CA_TEST_S3_ROOT; fi
if [[ $dst == s3://* ]]; then dst=$CA_TEST_S3_ROOT; fi
mkdir -p "$dst"
if compgen -G "$src/*" >/dev/null; then cp "$src/"* "$dst/"; fi
AWS
chmod +x "$ec_order_tmp/bin/aws"
EC_ORDER_S3=(ec-order --p 97 --a 2 --b 3 --state-dir "$ec_order_tmp/s3-local" \
  --s3-uri s3://test/ec-order --sync-every 1)
PATH="$ec_order_tmp/bin:$PATH" CA_TEST_S3_ROOT="$ec_order_tmp/remote" \
  want_no '"status":"limit reached"' "${EC_ORDER_S3[@]}" --max-work 20
rm -rf "$ec_order_tmp/s3-local"
PATH="$ec_order_tmp/bin:$PATH" CA_TEST_S3_ROOT="$ec_order_tmp/remote" \
  want '"order":100' "${EC_ORDER_S3[@]}" --resume
checks=$((checks + 1))
if [ ! -s "$ec_order_tmp/remote/ec-order.ckpt" ] || \
   ! grep -q '"order":100' "$ec_order_tmp/remote/result.json"; then
  printf 'FAIL: ec-order S3 mirror or restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$ec_order_tmp/remote/ec-order.ckpt" "$ec_order_tmp/remote-good.ckpt"
printf X >>"$ec_order_tmp/s3-local/ec-order.ckpt"
PATH="$ec_order_tmp/bin:$PATH" CA_TEST_S3_ROOT="$ec_order_tmp/remote" \
  want_bad 'ec-order checkpoint failed validation before S3 sync' \
  "${EC_ORDER_S3[@]}" --resume
checks=$((checks + 1))
if ! cmp -s "$ec_order_tmp/remote/ec-order.ckpt" "$ec_order_tmp/remote-good.ckpt"; then
  printf 'FAIL: invalid local ec-order checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
cp "$ec_order_tmp/remote-good.ckpt" "$ec_order_tmp/s3-local/ec-order.ckpt"
cp "$ec_order_tmp/remote/order-factor.ckpt" "$ec_order_tmp/remote-factor-good.ckpt"
printf X >>"$ec_order_tmp/s3-local/order-factor.ckpt"
PATH="$ec_order_tmp/bin:$PATH" CA_TEST_S3_ROOT="$ec_order_tmp/remote" \
  want_bad 'order factor checkpoint failed validation before S3 sync' \
  "${EC_ORDER_S3[@]}" --resume
checks=$((checks + 1))
if ! cmp -s "$ec_order_tmp/remote/order-factor.ckpt" "$ec_order_tmp/remote-factor-good.ckpt"; then
  printf 'FAIL: invalid local order factor checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$ec_order_tmp"
# x = 5 is not the x of a point of this curve; some x is, and the command must
# distinguish the two cases rather than guessing.
want_no '"on_curve":false' group lift-x "${EC[@]}" --x 5
lifted=0
for x in $(seq 1 40); do
  if "$CA" group lift-x "${EC[@]}" --x "$x" >/dev/null 2>&1; then
    want '"on_curve":true' group lift-x "${EC[@]}" --x "$x"
    lifted=1
    break
  fi
done
checks=$((checks + 1))
if [ "$lifted" -ne 1 ]; then
  echo 'FAIL no x in 1..40 lifted to a curve point' >&2
  fail=$((fail + 1))
fi
want_fail group lift-x "${ZP[@]}" --x 5           # lift-x is EC-only
want_fail group nonsense "${ZP[@]}"

# ── key generation and the solvers ──────────────────────────────────────────
want '"h"' gen "${ZP[@]}" --x 123456 --seed 1
want '"generator_trials"' gen "${ZP[@]}" --x 123456 --seed 1 --verbose
want '"cofactor":20' gen --group ec --p 97 --a 2 --b 3 --order 5 \
  --seed 1 --x 7 --verbose
gen_tmp=$(mktemp -d)
GEN=(gen --group ec --p 97 --a 2 --b 3 --seed 1 --x 7 \
  --state-dir "$gen_tmp/local" --progress-every 1 --checkpoint-every 1)
want_no '"status":"limit reached"' "${GEN[@]}" --max-count-work 20
checks=$((checks + 1))
if [ ! -s "$gen_tmp/local/gen.ckpt" ] || \
   ! grep -q '"field_x":20' "$gen_tmp/local/gen.count.ckpt.progress.json"; then
  printf 'FAIL: gen point-count checkpoint or progress missing\n' >&2
  fail=$((fail + 1))
fi
want '"order":5' "${GEN[@]}" --resume
checks=$((checks + 1))
if [ ! -s "$gen_tmp/local/gen.full-factor.ckpt" ] || \
   [ ! -s "$gen_tmp/local/gen.order-factor.ckpt" ] || \
   ! grep -q '"phase":"complete"' "$gen_tmp/local/result.json"; then
  printf 'FAIL: gen resume did not persist all phase artifacts\n' >&2
  fail=$((fail + 1))
fi
want '"order":5' "${GEN[@]}" --resume
want_bad 'run manifest does not match' gen --group ec --p 97 --a 2 --b 3 \
  --seed 1 --x 8 --state-dir "$gen_tmp/local" --resume
GEN_FACTOR=(gen --group ec --p 1000003 --a 2 --b 3 --seed 1 --x 42 \
  --state-dir "$gen_tmp/factor-local")
want_no '"status":"limit reached"' "${GEN_FACTOR[@]}" --max-factor-steps 3
checks=$((checks + 1))
if [ ! -s "$gen_tmp/factor-local/gen.count.ckpt" ] || \
   [ ! -s "$gen_tmp/factor-local/gen.full-factor.ckpt" ]; then
  printf 'FAIL: gen factor cap did not save count and factor checkpoints\n' >&2
  fail=$((fail + 1))
fi
cp -R "$gen_tmp/factor-local" "$gen_tmp/lag-local"
want '"order":367' "${GEN_FACTOR[@]}" --resume
cp "$gen_tmp/factor-local/gen.order-factor.ckpt" \
  "$gen_tmp/lag-local/gen.order-factor.ckpt"
mkdir "$gen_tmp/bin" "$gen_tmp/remote"
cat >"$gen_tmp/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
src=$3 dst=$4
if [[ $src == s3://* ]]; then src=$CA_TEST_S3_ROOT; fi
if [[ $dst == s3://* ]]; then dst=$CA_TEST_S3_ROOT; fi
mkdir -p "$dst"
if compgen -G "$src/*" >/dev/null; then cp "$src/"* "$dst/"; fi
AWS
chmod +x "$gen_tmp/bin/aws"
mkdir "$gen_tmp/remote-lag"
GEN_LAG=(gen --group ec --p 1000003 --a 2 --b 3 --seed 1 --x 42 \
  --state-dir "$gen_tmp/lag-local" --s3-uri s3://test/gen-lag --sync-every 1)
PATH="$gen_tmp/bin:$PATH" CA_TEST_S3_ROOT="$gen_tmp/remote-lag" \
  want '"order":367' "${GEN_LAG[@]}" --resume
checks=$((checks + 1))
if ! grep -q '"phase":"complete"' "$gen_tmp/remote-lag/result.json"; then
  printf 'FAIL: gen did not recover a child checkpoint ahead of its parent\n' >&2
  fail=$((fail + 1))
fi
GEN_S3=(gen --group ec --p 97 --a 2 --b 3 --seed 1 --x 7 \
  --state-dir "$gen_tmp/s3-local" --s3-uri s3://test/gen --sync-every 1)
PATH="$gen_tmp/bin:$PATH" CA_TEST_S3_ROOT="$gen_tmp/remote" \
  want_no '"status":"limit reached"' "${GEN_S3[@]}" --max-count-work 20
rm -rf "$gen_tmp/s3-local"
PATH="$gen_tmp/bin:$PATH" CA_TEST_S3_ROOT="$gen_tmp/remote" \
  want '"order":5' "${GEN_S3[@]}" --resume
checks=$((checks + 1))
if [ ! -s "$gen_tmp/remote/gen.ckpt" ] || \
   ! grep -q '"phase":"complete"' "$gen_tmp/remote/result.json"; then
  printf 'FAIL: gen S3 mirror or restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$gen_tmp/remote/gen.ckpt" "$gen_tmp/remote-good.ckpt"
printf X >>"$gen_tmp/s3-local/gen.ckpt"
PATH="$gen_tmp/bin:$PATH" CA_TEST_S3_ROOT="$gen_tmp/remote" \
  want_bad 'gen checkpoint failed validation before S3 sync' "${GEN_S3[@]}" --resume
checks=$((checks + 1))
if ! cmp -s "$gen_tmp/remote/gen.ckpt" "$gen_tmp/remote-good.ckpt"; then
  printf 'FAIL: invalid local gen checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
cp "$gen_tmp/remote-good.ckpt" "$gen_tmp/s3-local/gen.ckpt"
cp "$gen_tmp/remote/gen.count.ckpt" "$gen_tmp/remote-count-good.ckpt"
printf X >>"$gen_tmp/s3-local/gen.count.ckpt"
PATH="$gen_tmp/bin:$PATH" CA_TEST_S3_ROOT="$gen_tmp/remote" \
  want_bad 'gen count checkpoint failed validation before S3 sync' \
  "${GEN_S3[@]}" --resume
checks=$((checks + 1))
if ! cmp -s "$gen_tmp/remote/gen.count.ckpt" "$gen_tmp/remote-count-good.ckpt"; then
  printf 'FAIL: invalid local gen count checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$gen_tmp"
for alg in bsgs rho kangaroo grumpy dlog; do
  # x = 123456 is planted; every algorithm must find exactly it.
  want '"x":123456' solve --alg "$alg" "${ZP[@]}" --g 858101 \
    --h "$("$CA" group exp "${ZP[@]}" --elem 858101 --k 123456 | sed 's/.*"\([0-9]*\)".*/\1/')" \
    --lo 0 --hi 1000002 --seed 1
done
# The public algorithm commands share the solver implementation and result
# contract with `solve --alg`, including exact scalar recovery.
want '"x":123456' bsgs "${ZP[@]}" --g 858101 \
  --h "$("$CA" group exp "${ZP[@]}" --elem 858101 --k 123456 | sed 's/.*"\([0-9]*\)".*/\1/')"
want '"x":123456' rho "${ZP[@]}" --g 858101 \
  --h "$("$CA" group exp "${ZP[@]}" --elem 858101 --k 123456 | sed 's/.*"\([0-9]*\)".*/\1/')" \
  --seed 1
rho_tmp=$(mktemp -d)
RHO=(rho --group zp --p 1019 --order 509 --g 4 --h 818 --seed 1984 \
  --dp-bits 0 --walks 4 --state-dir "$rho_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${RHO[@]}" --max-ops 20
want '"x":177' "${RHO[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$rho_tmp/manifest.json" ] || [ ! -s "$rho_tmp/rho.dp" ] || \
   [ ! -s "$rho_tmp/rho.dp.progress.json" ] || [ ! -s "$rho_tmp/result.json" ]; then
  printf 'FAIL: rho checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' rho --group zp --p 1019 --order 509 \
  --g 4 --h 818 --seed 1985 --dp-bits 0 --walks 4 --state-dir "$rho_tmp" --resume
want_bad 'live progress and resumable state require --alg' \
  solve --alg unsupported --group zp --p 1019 --order 509 --g 4 --h 818 --state-dir "$rho_tmp"
rm -rf "$rho_tmp"
precomp_tmp=$(mktemp -d)
PRECOMP=(solve --alg precomp --group zp --p 1019 --order 509 --g 4 --h 818 \
  --seed 17 --table 64 --state-dir "$precomp_tmp")
want '"x":177' "${PRECOMP[@]}"
want '"x":177' "${PRECOMP[@]}" --resume
checks=$((checks + 1))
if [ ! -s "$precomp_tmp/precomp.table.ckpt" ] || \
   [ ! -s "$precomp_tmp/precomp.online.ckpt" ] || \
   [ ! -s "$precomp_tmp/result.json" ]; then
  printf 'FAIL: precomp checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$precomp_tmp"
bsgs_tmp=$(mktemp -d)
BSGS=(bsgs "${ZP[@]}" --g 858101 --h 218146 --lo 0 --hi 1000001 \
  --state-dir "$bsgs_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${BSGS[@]}" --max-ops 100
want '"x":123456' "${BSGS[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$bsgs_tmp/manifest.json" ] || [ ! -s "$bsgs_tmp/bsgs.ckpt" ] || \
   [ ! -s "$bsgs_tmp/bsgs.ckpt.progress.json" ] || [ ! -s "$bsgs_tmp/result.json" ]; then
  printf 'FAIL: bsgs checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' bsgs "${ZP[@]}" --g 858101 --h 218146 \
  --lo 0 --hi 1000001 --table 17 --state-dir "$bsgs_tmp" --resume
rm -rf "$bsgs_tmp"
grumpy_tmp=$(mktemp -d)
GRUMPY=(grumpy --group zp --p 1019 --order 509 --g 4 --h 818 \
  --lo 0 --hi 508 --state-dir "$grumpy_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${GRUMPY[@]}" --max-ops 20
want '"x":177' "${GRUMPY[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$grumpy_tmp/manifest.json" ] || [ ! -s "$grumpy_tmp/grumpy.ckpt" ] || \
   [ ! -s "$grumpy_tmp/grumpy.ckpt.progress.json" ] || [ ! -s "$grumpy_tmp/result.json" ]; then
  printf 'FAIL: grumpy checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' grumpy --group zp --p 1019 --order 509 \
  --g 4 --h 818 --lo 0 --hi 507 --state-dir "$grumpy_tmp" --resume
rm -rf "$grumpy_tmp"
kangaroo_tmp=$(mktemp -d)
KANGAROO=(kangaroo --group zp --p 1019 --order 509 --g 4 --h 818 \
  --lo 0 --hi 508 --seed 17 --dp-bits 0 --herd 2 \
  --state-dir "$kangaroo_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${KANGAROO[@]}" --max-ops 40
want '"x":177' "${KANGAROO[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$kangaroo_tmp/manifest.json" ] || [ ! -s "$kangaroo_tmp/kangaroo.ckpt" ] || \
   [ ! -s "$kangaroo_tmp/kangaroo.ckpt.progress.json" ] || \
   [ ! -s "$kangaroo_tmp/result.json" ]; then
  printf 'FAIL: kangaroo checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' kangaroo --group zp --p 1019 --order 509 \
  --g 4 --h 818 --lo 0 --hi 507 --seed 17 --dp-bits 0 --herd 2 \
  --state-dir "$kangaroo_tmp" --resume
rm -rf "$kangaroo_tmp"
kangaroo_s3_test=$(mktemp -d)
mkdir "$kangaroo_s3_test/bin" "$kangaroo_s3_test/remote"
cat > "$kangaroo_s3_test/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
src=$3 dst=$4
if [[ $src == s3://* ]]; then src=$CA_TEST_S3_ROOT; fi
if [[ $dst == s3://* ]]; then dst=$CA_TEST_S3_ROOT; fi
mkdir -p "$dst"
if compgen -G "$src/*" >/dev/null; then cp "$src/"* "$dst/"; fi
AWS
chmod +x "$kangaroo_s3_test/bin/aws"
KANGAROO_S3=(kangaroo --group zp --p 1019 --order 509 --g 4 --h 818 \
  --lo 0 --hi 508 --seed 17 --dp-bits 0 --herd 2 \
  --state-dir "$kangaroo_s3_test/local" --s3-uri s3://test/kangaroo --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${KANGAROO_S3[@]}" --max-ops 40
rm -rf "$kangaroo_s3_test/local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":177' "${KANGAROO_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$kangaroo_s3_test/remote/kangaroo.ckpt" ] || \
   ! grep -q '"x":177' "$kangaroo_s3_test/remote/result.json"; then
  printf 'FAIL: kangaroo S3 mirror/restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
rm -f "$kangaroo_s3_test/remote/"*
BSGS_S3=(bsgs "${ZP[@]}" --g 858101 --h 218146 --lo 0 --hi 1000001 \
  --state-dir "$kangaroo_s3_test/bsgs-local" --s3-uri s3://test/bsgs --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${BSGS_S3[@]}" --max-ops 100
rm -rf "$kangaroo_s3_test/bsgs-local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":123456' "${BSGS_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$kangaroo_s3_test/remote/bsgs.ckpt" ] || \
   ! grep -q '"x":123456' "$kangaroo_s3_test/remote/result.json"; then
  printf 'FAIL: bsgs S3 mirror/restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
rm -f "$kangaroo_s3_test/remote/"*
RHO_S3=(rho --group zp --p 1019 --order 509 --g 4 --h 818 --seed 1984 \
  --dp-bits 0 --walks 4 --state-dir "$kangaroo_s3_test/rho-local" \
  --s3-uri s3://test/rho --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${RHO_S3[@]}" --max-ops 20
rm -rf "$kangaroo_s3_test/rho-local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":177' "${RHO_S3[@]}" --max-ops 100000 --resume
cp "$kangaroo_s3_test/remote/rho.dp" "$kangaroo_s3_test/rho-good"
printf X >> "$kangaroo_s3_test/rho-local/rho.dp"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_bad 'walk checkpoint failed validation before S3 sync' \
  "${RHO_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$kangaroo_s3_test/remote/rho.dp" "$kangaroo_s3_test/rho-good"; then
  printf 'FAIL: corrupt local rho checkpoint replaced S3 copy\n' >&2
  fail=$((fail + 1))
fi
want_fail bsgs --alg rho "${ZP[@]}" --g 858101 --h 123456
want_fail rho --curve unknown
want_fail rho --curve ecc2k130 --backend unknown
want_fail rho --curve ecc2k130 --backend metal --kat fixture

# Exercise the packaged ECC2K wrappers without needing a GPU or S3 account.
# The stub uses the same checkpoint/corpus paths as the real kernels.
ecc_tmp=$(mktemp -d)
mkdir -p "$ecc_tmp/pkg/bin" "$ecc_tmp/pkg/libexec/cryptanalysis" "$ecc_tmp/awsbin" "$ecc_tmp/remote"
cp "$CA" "$ecc_tmp/pkg/bin/cryptanalysis"
cat >"$ecc_tmp/pkg/libexec/cryptanalysis/ecc2k130-rho-cuda" <<'SH'
#!/bin/sh
set -eu
[ "$1" = walk ] || exit 2
shift
dp= ck= id=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dp-file|--dp-file32) dp=$2; shift 2 ;;
    --checkpoint) ck=$2; shift 2 ;;
    --run-id) id=$2; shift 2 ;;
    *) shift ;;
  esac
done
[ "$id" = 7 ] && [ -n "$dp" ] && [ -n "$ck" ] || exit 2
if [ -f "$ck" ]; then printf 'backend resumed\n' >&2; fi
dd if=/dev/zero bs=32 count=1 2>/dev/null >>"$dp"
printf 'checkpoint 7\n' >"$ck"
sleep 2
SH
chmod +x "$ecc_tmp/pkg/libexec/cryptanalysis/ecc2k130-rho-cuda"
cp "$ecc_tmp/pkg/libexec/cryptanalysis/ecc2k130-rho-cuda" \
  "$ecc_tmp/pkg/libexec/cryptanalysis/ecc2k130-rho-metal"
cat >"$ecc_tmp/awsbin/aws" <<'SH'
#!/bin/sh
set -eu
[ "$1" = s3 ] || exit 2
verb=$2; from=$3; to=$4
case "$from" in
  s3://test/ecc2k) from=$CA_TEST_S3_REMOTE ;;
  s3://test/ecc2k/*) from="$CA_TEST_S3_REMOTE/${from#s3://test/ecc2k/}" ;;
esac
case "$to" in
  s3://test/ecc2k) to=$CA_TEST_S3_REMOTE ;;
  s3://test/ecc2k/*) to="$CA_TEST_S3_REMOTE/${to#s3://test/ecc2k/}" ;;
esac
if [ "$verb" = ls ]; then
  if [ -d "$from" ]; then find "$from" -type f -print; fi
elif [ "$verb" = sync ]; then
  if [ -d "$from" ]; then
    mkdir -p "$to"
    cp -R "$from/." "$to/"
  fi
else
  mkdir -p "$(dirname "$to")"
  cp "$from" "$to"
  printf '%s\n' "$(basename "$to")" >>"$CA_TEST_S3_LOG"
fi
SH
chmod +x "$ecc_tmp/awsbin/aws"
ecc_ca="$ecc_tmp/pkg/bin/cryptanalysis"
ecc_state="$ecc_tmp/state"
export CA_TEST_S3_REMOTE="$ecc_tmp/remote" CA_TEST_S3_LOG="$ecc_tmp/upload.log"
checks=$((checks + 1))
ecc_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" rho --curve ecc2k130 --backend cuda \
  --run-id 7 --verbose --progress-every 1 --state-dir "$ecc_state" \
  --s3-uri s3://test/ecc2k --sync-every 1 2>&1) || {
  printf 'FAIL: ECC2K managed first run: %s\n' "$ecc_out" >&2; fail=$((fail + 1));
}
if [[ "$ecc_out" != *'dp_bytes='* ]] || [ ! -f "$ecc_state/state.ck" ] || \
   [ ! -f "$ecc_tmp/remote/state.ck" ] || [ "$(wc -c <"$ecc_state/dps.bin")" -ne 32 ]; then
  printf 'FAIL: ECC2K managed progress or artifacts missing\n' >&2; fail=$((fail + 1))
fi
checks=$((checks + 1))
first_dp=$(awk '/^dps.bin$/{print NR; exit}' "$ecc_tmp/upload.log")
first_ck=$(awk '/^state.ck$/{print NR; exit}' "$ecc_tmp/upload.log")
if [ -z "$first_dp" ] || [ -z "$first_ck" ] || [ "$first_dp" -ge "$first_ck" ]; then
  printf 'FAIL: ECC2K S3 corpus was not uploaded before checkpoint\n' >&2; fail=$((fail + 1))
fi
printf x >>"$ecc_tmp/remote/dps.bin"
rm -rf "$ecc_state"
checks=$((checks + 1))
ecc_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" rho --curve ecc2k130 --backend cuda \
  --run-id 7 --resume --state-dir "$ecc_state" --s3-uri s3://test/ecc2k 2>&1) || {
  printf 'FAIL: ECC2K S3 restore: %s\n' "$ecc_out" >&2; fail=$((fail + 1));
}
if [[ "$ecc_out" != *'backend resumed'* ]] || \
   [[ "$ecc_out" != *'discarded 1 partial corpus bytes'* ]] || \
   [ "$(wc -c <"$ecc_state/dps.bin")" -ne 64 ]; then
  printf 'FAIL: ECC2K S3 restore did not continue the corpus\n' >&2; fail=$((fail + 1))
fi
CA="$ecc_ca" want_bad 'run manifest does not match' rho --curve ecc2k130 --backend cuda \
  --run-id 8 --resume --state-dir "$ecc_state"
metal_state="$ecc_tmp/metal"
: >"$ecc_tmp/upload.log"
checks=$((checks + 1))
ecc_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" rho --curve ecc2k130 --backend metal \
  --run-id 7 --verbose --progress-every 1 --state-dir "$metal_state" \
  --s3-uri s3://test/ecc2k/metal --sync-every 1 2>&1) || {
  printf 'FAIL: ECC2K Metal managed first run: %s\n' "$ecc_out" >&2; fail=$((fail + 1));
}
if [[ "$ecc_out" != *'[ecc2k130/metal]'* ]] || [ ! -f "$metal_state/state.ck" ] || \
   [ ! -f "$ecc_tmp/remote/metal/state.ck" ] || \
   [ "$(wc -c <"$metal_state/dps.bin")" -ne 32 ] || \
   ! grep -q '"backend":"metal"' "$metal_state/progress.json" || \
   ! grep -q '"backend":"metal"' "$metal_state/result.json"; then
  printf 'FAIL: ECC2K Metal managed progress or artifacts missing\n' >&2; fail=$((fail + 1))
fi
checks=$((checks + 1))
metal_dp=$(awk '/^dps.bin$/{print NR; exit}' "$ecc_tmp/upload.log")
metal_ck=$(awk '/^state.ck$/{print NR; exit}' "$ecc_tmp/upload.log")
if [ -z "$metal_dp" ] || [ -z "$metal_ck" ] || [ "$metal_dp" -ge "$metal_ck" ]; then
  printf 'FAIL: ECC2K Metal S3 corpus was not uploaded before checkpoint\n' >&2
  fail=$((fail + 1))
fi
printf x >>"$ecc_tmp/remote/metal/dps.bin"
rm -rf "$metal_state"
checks=$((checks + 1))
ecc_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" rho --curve ecc2k130 --backend metal \
  --run-id 7 --resume --state-dir "$metal_state" --s3-uri s3://test/ecc2k/metal 2>&1) || {
  printf 'FAIL: ECC2K Metal S3 restore: %s\n' "$ecc_out" >&2; fail=$((fail + 1));
}
if [[ "$ecc_out" != *'backend resumed'* ]] || \
   [[ "$ecc_out" != *'discarded 1 partial corpus bytes'* ]] || \
   [ "$(wc -c <"$metal_state/dps.bin")" -ne 64 ]; then
  printf 'FAIL: ECC2K Metal S3 restore did not continue the corpus\n' >&2; fail=$((fail + 1))
fi
CA="$ecc_ca" want_bad 'run manifest does not match' rho --curve ecc2k130 --backend cuda \
  --run-id 7 --resume --state-dir "$metal_state"
CA="$ecc_ca" want_bad '--run-id must be at most 65535' rho --curve ecc2k130 \
  --backend metal --run-id 65536 --state-dir "$ecc_tmp/bad-id"

# A solo distributed worker must retain its verified CRDT check-ins and
# cursors across a process restart, including an S3-only restore.
"$ecc_ca" coord-job --group zp --p 1000003 --order 1000002 --g 858101 --h 218146 \
  --dp-bits 4 --unit-size 2 --seed 42 --out "$ecc_tmp/work-job.txt" >/dev/null
work_state="$ecc_tmp/work-state"
checks=$((checks + 1))
work_rc=0
work_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" work --job "$ecc_tmp/work-job.txt" \
  --node fixture --max-walkers 2 --max-seconds 1 --state-dir "$work_state" \
  --verbose --progress-every 1 --checkpoint-every 1 \
  --s3-uri s3://test/ecc2k/work --sync-every 1 2>&1) || work_rc=$?
if { [ "$work_rc" -ne 0 ] && [ "$work_rc" -ne 3 ]; } || \
   [[ "$work_out" != *'[work]'* ]] || \
   [ ! -s "$work_state/checkins.log" ] || \
   [ ! -s "$ecc_tmp/remote/work/checkins.log" ] || \
   [ ! -f "$ecc_tmp/remote/work/result.json" ] || \
   ! grep -q '"units_completed":1' "$work_state/progress.json"; then
  printf 'FAIL: work progress or S3 journal missing (rc=%d): %s\n' "$work_rc" "$work_out" >&2
  fail=$((fail + 1))
fi
first_lines=$(wc -l <"$work_state/checkins.log")
printf x >>"$ecc_tmp/remote/work/checkins.log"
rm -rf "$work_state"
checks=$((checks + 1))
work_rc=0
work_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" work --job "$ecc_tmp/work-job.txt" \
  --node fixture --max-walkers 2 --max-seconds 1 --state-dir "$work_state" \
  --resume --s3-uri s3://test/ecc2k/work 2>&1) || work_rc=$?
second_lines=$(wc -l <"$work_state/checkins.log")
if { [ "$work_rc" -ne 0 ] && [ "$work_rc" -ne 3 ]; } || \
   [ "$second_lines" -lt "$first_lines" ] || \
   [ ! -f "$work_state/progress.json" ] || [ ! -f "$work_state/result.json" ] || \
   grep -q '"status":"running"' "$work_state/progress.json"; then
  printf 'FAIL: work S3 journal restore (rc=%d): %s\n' "$work_rc" "$work_out" >&2
  fail=$((fail + 1))
fi
rm -rf "$ecc_tmp/remote/work"
checks=$((checks + 1))
work_rc=0
work_out=$(PATH="$ecc_tmp/awsbin:$PATH" "$ecc_ca" work --job "$ecc_tmp/work-job.txt" \
  --node fixture --max-walkers 2 --max-seconds 1 --state-dir "$work_state" \
  --resume --s3-uri s3://test/ecc2k/work 2>&1) || work_rc=$?
if { [ "$work_rc" -ne 0 ] && [ "$work_rc" -ne 3 ]; } || \
   [ ! -f "$ecc_tmp/remote/work/manifest.json" ]; then
  printf 'FAIL: work could not seed an empty S3 prefix (rc=%d): %s\n' \
    "$work_rc" "$work_out" >&2
  fail=$((fail + 1))
fi
"$ecc_ca" coord-job --group zp --p 1000003 --order 1000002 --g 858101 --h 218146 \
  --dp-bits 4 --unit-size 2 --seed 43 --out "$ecc_tmp/other-job.txt" >/dev/null
CA="$ecc_ca" want_bad 'work manifest does not match' work --job "$ecc_tmp/other-job.txt" \
  --state-dir "$work_state" --resume
printf '{"bad":true}\n' >"$ecc_tmp/remote/work/manifest.json"
PATH="$ecc_tmp/awsbin:$PATH" CA="$ecc_ca" \
  want_bad 'S3 work manifest is unavailable or does not match' work \
  --job "$ecc_tmp/work-job.txt" --state-dir "$work_state" --resume \
  --s3-uri s3://test/ecc2k/work
printf 'not-a-checkin\n' >>"$work_state/checkins.log"
CA="$ecc_ca" want_bad 'work check-in journal is missing or invalid' work \
  --job "$ecc_tmp/work-job.txt" --state-dir "$work_state" --resume
rm -rf "$ecc_tmp"
unset CA_TEST_S3_REMOTE CA_TEST_S3_LOG
want '"x":123456' solve --alg gpu-rho "${ZP[@]}" --g 858101 \
  --h "$("$CA" group exp "${ZP[@]}" --elem 858101 --k 123456 | sed 's/.*"\([0-9]*\)".*/\1/')" \
  --seed 1
gpu_tmp=$(mktemp -d)
GPU_RHO=(solve --alg gpu-rho "${ZP[@]}" --g 858101 --h 218146 \
  --backend emulate --seed 3 --blocks 1 --tpb 4 --steps 16 --dp-bits 2 \
  --state-dir "$gpu_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${GPU_RHO[@]}" --max-ops 1000
want '"x":123456' "${GPU_RHO[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$gpu_tmp/gpu-rho.dp" ] || \
   [ ! -s "$gpu_tmp/gpu-rho.dp.progress.json" ] || \
   ! grep -q '"x":123456' "$gpu_tmp/result.json"; then
  printf 'FAIL: GPU rho checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' solve --alg gpu-rho "${ZP[@]}" \
  --g 858101 --h 218146 --backend emulate --seed 4 --blocks 1 --tpb 4 \
  --steps 16 --dp-bits 2 --state-dir "$gpu_tmp" --resume
printf X >> "$gpu_tmp/gpu-rho.dp"
cp "$gpu_tmp/gpu-rho.dp" "$gpu_tmp/corrupt-copy"
want_bad 'GPU rho checkpoint failed validation before S3 sync' "${GPU_RHO[@]}" \
  --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$gpu_tmp/gpu-rho.dp" "$gpu_tmp/corrupt-copy"; then
  printf 'FAIL: invalid GPU rho checkpoint was overwritten\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$gpu_tmp"
want_fail solve --alg dlog --group zp --p 12x34    # malformed number

# Bernstein-Lange precomputation (ca_precomp.h).  The method needs a base that
# generates the whole group, so work in the prime-order subgroup (order 166667,
# where 1000002 = 2 * 3 * 166667): g^6 is such a base.  Plant x = 12345 and
# solve it online against the precomputed table.
PSUB=(--group zp --p 1000003 --order 166667)
PBASE=$("$CA" group exp "${ZP[@]}" --elem 858101 --k 6 | sed 's/.*"\([0-9]*\)".*/\1/')
PH=$("$CA" group exp "${PSUB[@]}" --elem "$PBASE" --k 12345 | sed 's/.*"\([0-9]*\)".*/\1/')
want '"precomp_ops"' solve --alg precomp "${PSUB[@]}" --g "$PBASE" --h "$PH" --seed 1
want '"x":12345' solve --alg precomp "${PSUB[@]}" --g "$PBASE" --h "$PH" --seed 1

# Curve-aware dispatch (ca_curve.h): the GLV endomorphism families are
# detected from name or parameters, and solve --alg glv folds the rho walk.
want '"endomorphism":"j0"' curve --name glv-j0-26
want '"endomorphism":"j1728"' curve --name glv-j1728-26
want '"endomorphism":"none"' curve --name generic-26
want '"aut_order":6' curve --group ec --p 67108933 --a 0 --b 7 --order 16773703
want '"curves"' curve --list
want_no '"status":"not found"' curve --name no-such-curve
CJ0=(--group ec --p 67108933 --a 0 --b 7 --order 16773703)
GJ0=$("$CA" group generator "${CJ0[@]}" | sed 's/.*"generator":"\([^"]*\)".*/\1/')
HJ0=$("$CA" group exp "${CJ0[@]}" --elem "$GJ0" --k 424242 | sed 's/.*"result":"\([^"]*\)".*/\1/')
want '"x":424242' solve --alg glv "${CJ0[@]}" --g "$GJ0" --h "$HJ0" --seed 3
want '"endomorphism":"j0"' solve --alg glv "${CJ0[@]}" --g "$GJ0" --h "$HJ0" --seed 3
glv_tmp=$(mktemp -d)
GLV=(solve --alg glv "${CJ0[@]}" --g "$GJ0" --h "$HJ0" --seed 3 \
  --state-dir "$glv_tmp" --verbose --progress-every 1)
want_no '"status":"limit reached"' "${GLV[@]}" --max-ops 1000
want '"x":424242' "${GLV[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$glv_tmp/glv.ckpt" ] || [ ! -s "$glv_tmp/glv.ckpt.progress.json" ] || \
   ! grep -q '"x":424242' "$glv_tmp/result.json"; then
  printf 'FAIL: GLV checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cold_glv=$(
  "$CA" solve --alg glv "${CJ0[@]}" --g "$GJ0" --h "$HJ0" --seed 3 --max-ops 100000
)
cold_steps=$(printf '%s\n' "$cold_glv" | sed 's/.*"iterations":\([0-9]*\).*/\1/')
resumed_steps=$(sed 's/.*"iterations":\([0-9]*\).*/\1/' "$glv_tmp/result.json")
checks=$((checks + 1))
if [ "$cold_steps" != "$resumed_steps" ]; then
  printf 'FAIL: resumed GLV steps differ from uninterrupted walk\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' solve --alg glv "${CJ0[@]}" \
  --g "$GJ0" --h "$HJ0" --seed 4 --state-dir "$glv_tmp" --resume
printf X >> "$glv_tmp/glv.ckpt"
cp "$glv_tmp/glv.ckpt" "$glv_tmp/corrupt-copy"
want_bad 'walk checkpoint failed validation before S3 sync' \
  "${GLV[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$glv_tmp/glv.ckpt" "$glv_tmp/corrupt-copy"; then
  printf 'FAIL: invalid GLV checkpoint was overwritten\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$glv_tmp"
rm -f "$kangaroo_s3_test/remote/"*
GLV_S3=(solve --alg glv "${CJ0[@]}" --g "$GJ0" --h "$HJ0" --seed 3 \
  --state-dir "$kangaroo_s3_test/glv-local" --s3-uri s3://test/glv --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${GLV_S3[@]}" --max-ops 1000
rm -rf "$kangaroo_s3_test/glv-local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":424242' "${GLV_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$kangaroo_s3_test/remote/glv.ckpt" ] || \
   ! grep -q '"x":424242' "$kangaroo_s3_test/remote/result.json"; then
  printf 'FAIL: GLV S3 mirror/restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$kangaroo_s3_test/remote/glv.ckpt" "$kangaroo_s3_test/glv-good"
printf X >> "$kangaroo_s3_test/glv-local/glv.ckpt"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_bad 'walk checkpoint failed validation before S3 sync' \
  "${GLV_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$kangaroo_s3_test/remote/glv.ckpt" "$kangaroo_s3_test/glv-good"; then
  printf 'FAIL: corrupt local GLV checkpoint replaced S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -f "$kangaroo_s3_test/remote/"*
CG=(--group ec --p 67108879 --a 2 --b 3 --order 3355777)
GG=$("$CA" group generator "${CG[@]}" | sed 's/.*"generator":"\([^"]*\)".*/\1/')
HG=$("$CA" group exp "${CG[@]}" --elem "$GG" --k 1234 | sed 's/.*"result":"\([^"]*\)".*/\1/')
GENERIC_S3=(solve --alg glv "${CG[@]}" --g "$GG" --h "$HG" --seed 7 \
  --state-dir "$kangaroo_s3_test/generic-local" --s3-uri s3://test/generic \
  --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${GENERIC_S3[@]}" --max-ops 100
rm -rf "$kangaroo_s3_test/generic-local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":1234' "${GENERIC_S3[@]}" --max-ops 100000 --resume
cp "$kangaroo_s3_test/remote/glv.ckpt" "$kangaroo_s3_test/generic-good"
printf X >> "$kangaroo_s3_test/generic-local/glv.ckpt"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_bad 'walk checkpoint failed validation before S3 sync' \
  "${GENERIC_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$kangaroo_s3_test/remote/glv.ckpt" "$kangaroo_s3_test/generic-good"; then
  printf 'FAIL: corrupt generic-curve checkpoint replaced S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -f "$kangaroo_s3_test/remote/"*
GPU_S3=(solve --alg gpu-rho "${ZP[@]}" --g 858101 --h 218146 \
  --backend emulate --seed 3 --blocks 1 --tpb 4 --steps 16 --dp-bits 2 \
  --state-dir "$kangaroo_s3_test/gpu-local" --s3-uri s3://test/gpu-rho --sync-every 1)
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_no '"status":"limit reached"' "${GPU_S3[@]}" --max-ops 1000
rm -rf "$kangaroo_s3_test/gpu-local"
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want '"x":123456' "${GPU_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if [ ! -s "$kangaroo_s3_test/remote/gpu-rho.dp" ] || \
   ! grep -q '"x":123456' "$kangaroo_s3_test/remote/result.json"; then
  printf 'FAIL: GPU rho S3 mirror/restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$kangaroo_s3_test/remote/gpu-rho.dp" "$kangaroo_s3_test/gpu-good"
gpu_ckpt="$kangaroo_s3_test/gpu-local/gpu-rho.dp"
gpu_key_offset=$(( $(wc -c < "$gpu_ckpt") - 24 ))
gpu_key_byte=$(od -An -tu1 -j "$gpu_key_offset" -N1 "$gpu_ckpt")
if [ "$gpu_key_byte" -eq 1 ]; then gpu_changed_byte='\002'; else gpu_changed_byte='\001'; fi
printf "$gpu_changed_byte" | dd of="$gpu_ckpt" bs=1 seek="$gpu_key_offset" \
  conv=notrunc 2>/dev/null
PATH="$kangaroo_s3_test/bin:$PATH" CA_TEST_S3_ROOT="$kangaroo_s3_test/remote" \
  want_bad 'GPU rho checkpoint failed validation before S3 sync' \
  "${GPU_S3[@]}" --max-ops 100000 --resume
checks=$((checks + 1))
if ! cmp -s "$kangaroo_s3_test/remote/gpu-rho.dp" "$kangaroo_s3_test/gpu-good"; then
  printf 'FAIL: corrupt GPU rho checkpoint replaced S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$kangaroo_s3_test"

# ── index calculus ──────────────────────────────────────────────────────────
want '"status":"ok"' ic --p 1099511627791 --g 3 --h 123456789 --threads 2
want '"x":69,"check":3' ic --p 101 --g 2 --h 3 --method rexp --B 13 --seed 1 --threads 1
ic_tmp=$(mktemp -d)
want '"status":"ok"' ic --p 1000003 --g 2 --h 123456 --seed 7 --verbose \
  --state-dir "$ic_tmp" --progress-every 1
want '"status":"ok"' ic --p 1000003 --g 2 --h 123456 --seed 7 --verbose \
  --state-dir "$ic_tmp" --progress-every 1 --resume
checks=$((checks + 1))
if [ ! -s "$ic_tmp/relations.ckpt" ] || [ ! -s "$ic_tmp/relations.ckpt.precomp" ] || \
   [ ! -s "$ic_tmp/progress.json" ]; then
  printf 'FAIL: ic checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
# A remote copy must never replace a local run's mismatched identity.
ic_s3_test=$(mktemp -d)
mkdir "$ic_s3_test/bin" "$ic_s3_test/local" "$ic_s3_test/remote"
cp "$ic_tmp/"* "$ic_s3_test/remote/"
cat > "$ic_s3_test/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
touch "$CA_TEST_S3_CALLED"
if [[ $3 == s3://* ]]; then
  cp "$CA_TEST_S3_FIXTURE/"* "$4/"
else
  cp "$3/"* "$CA_TEST_S3_FIXTURE/"
fi
AWS
chmod +x "$ic_s3_test/bin/aws"
printf 'another run\n' > "$ic_s3_test/local/manifest.json"
cp "$ic_s3_test/local/manifest.json" "$ic_s3_test/original-manifest"
PATH="$ic_s3_test/bin:$PATH" CA_TEST_S3_FIXTURE="$ic_s3_test/remote" \
  CA_TEST_S3_CALLED="$ic_s3_test/called" \
  want_bad 'run manifest does not match these arguments' \
  ic --p 1000003 --g 2 --h 123456 --seed 7 --resume \
  --state-dir "$ic_s3_test/local" --s3-uri s3://test/checkpoint
checks=$((checks + 1))
if [ -e "$ic_s3_test/called" ] || \
   ! cmp -s "$ic_s3_test/original-manifest" "$ic_s3_test/local/manifest.json"; then
  printf 'FAIL: mismatched local manifest was exposed to S3 restore\n' >&2
  fail=$((fail + 1))
fi
rm "$ic_s3_test/local/manifest.json"
printf 'preserve\n' > "$ic_s3_test/local/unrelated"
PATH="$ic_s3_test/bin:$PATH" CA_TEST_S3_FIXTURE="$ic_s3_test/remote" \
  CA_TEST_S3_CALLED="$ic_s3_test/called" \
  want_bad 'nonempty directory without a run manifest' \
  ic --p 1000003 --g 2 --h 123456 --seed 7 --resume \
  --state-dir "$ic_s3_test/local" --s3-uri s3://test/checkpoint
checks=$((checks + 1))
if [ -e "$ic_s3_test/called" ] || [ -e "$ic_s3_test/local/manifest.json" ]; then
  printf 'FAIL: unidentified local files were exposed to S3 restore\n' >&2
  fail=$((fail + 1))
fi
rm "$ic_s3_test/local/unrelated"
PATH="$ic_s3_test/bin:$PATH" CA_TEST_S3_FIXTURE="$ic_s3_test/remote" \
  CA_TEST_S3_CALLED="$ic_s3_test/called" \
  want '"status":"ok"' ic --p 1000003 --g 2 --h 123456 --seed 7 --resume \
  --state-dir "$ic_s3_test/local" --s3-uri s3://test/checkpoint
cp "$ic_s3_test/remote/relations.ckpt" "$ic_s3_test/good-journal"
rm "$ic_s3_test/called"
printf X > "$ic_s3_test/local/relations.ckpt"
PATH="$ic_s3_test/bin:$PATH" CA_TEST_S3_FIXTURE="$ic_s3_test/remote" \
  CA_TEST_S3_CALLED="$ic_s3_test/called" \
  want_bad 'checkpoint failed validation before S3 sync' \
  ic --p 1000003 --g 2 --h 123456 --seed 7 --resume \
  --state-dir "$ic_s3_test/local" --s3-uri s3://test/checkpoint
checks=$((checks + 1))
if [ -e "$ic_s3_test/called" ] || \
   ! cmp -s "$ic_s3_test/remote/relations.ckpt" "$ic_s3_test/good-journal"; then
  printf 'FAIL: corrupt local IC journal reached S3\n' >&2
  fail=$((fail + 1))
fi
cp "$ic_s3_test/good-journal" "$ic_s3_test/local/relations.ckpt"
cp "$ic_s3_test/remote/relations.ckpt.precomp" "$ic_s3_test/good-precomp"
printf X >> "$ic_s3_test/local/relations.ckpt.precomp"
PATH="$ic_s3_test/bin:$PATH" CA_TEST_S3_FIXTURE="$ic_s3_test/remote" \
  CA_TEST_S3_CALLED="$ic_s3_test/called" \
  want_bad 'checkpoint failed validation before S3 sync' \
  ic --p 1000003 --g 2 --h 123456 --seed 7 --resume \
  --state-dir "$ic_s3_test/local" --s3-uri s3://test/checkpoint
checks=$((checks + 1))
if [ -e "$ic_s3_test/called" ] || \
   ! cmp -s "$ic_s3_test/remote/relations.ckpt.precomp" "$ic_s3_test/good-precomp"; then
  printf 'FAIL: corrupt local IC precomputation reached S3\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$ic_tmp" "$ic_s3_test"
rexp_tmp=$(mktemp -d)
want '"x":69' ic --p 101 --g 2 --h 3 --method rexp --B 13 --seed 1 \
  --state-dir "$rexp_tmp" --progress-every 1
want '"x":69' ic --p 101 --g 2 --h 3 --method rexp --B 13 --seed 1 \
  --state-dir "$rexp_tmp" --progress-every 1 --resume
rexp_s3=$(mktemp -d)
mkdir "$rexp_s3/bin" "$rexp_s3/remote"
cp "$rexp_tmp/"* "$rexp_s3/remote/"
cat > "$rexp_s3/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
touch "$CA_TEST_S3_CALLED"
if [[ $3 == s3://* ]]; then cp "$CA_TEST_S3_ROOT/"* "$4/"; fi
AWS
chmod +x "$rexp_s3/bin/aws"
printf X >> "$rexp_tmp/relations.ckpt"
PATH="$rexp_s3/bin:$PATH" CA_TEST_S3_ROOT="$rexp_s3/remote" \
  CA_TEST_S3_CALLED="$rexp_s3/called" \
  want_bad 'checkpoint failed validation before S3 sync' \
  ic --p 101 --g 2 --h 3 --method rexp --B 13 --seed 1 --resume \
  --state-dir "$rexp_tmp" --s3-uri s3://test/rexp
checks=$((checks + 1))
if [ -e "$rexp_s3/called" ]; then
  printf 'FAIL: corrupt local IC rexp snapshot reached S3\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$rexp_s3"
REXP=(ic --p 101 --g 2 --h 3 --method rexp --B 13 --seed 1 --threads 1 \
  --state-dir "$rexp_tmp" --progress-every 1)
want '"x":69,"check":3' "${REXP[@]}"
want '"x":69,"check":3' "${REXP[@]}" --resume
checks=$((checks + 1))
if [ ! -s "$rexp_tmp/relations.ckpt" ] || [ ! -s "$rexp_tmp/relations.ckpt.precomp" ]; then
  printf 'FAIL: rexp checkpoint artifacts missing\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$rexp_tmp"
want_bad '--max-relation-tries requires --method rexp' \
  ic --p 101 --g 2 --h 3 --method lsieve --max-relation-tries 1
want_bad '--method must be lsieve or rexp' ic --p 101 --g 2 --h 3 --method unknown
want_bad 'option requires a value' ic --p 101 --g 2 --h 3 --method
want_bad 'option value exceeds uint32 range' ic --p 101 --g 2 --h 3 --B 4294967296
want_bad 'option value must be nonnegative' ic --p -101 --g 2 --h 3
want_bad 'option value is not a valid uint64 integer' ic --p 18446744073709551616 --g 2 --h 3

# ── Cheon's attack ──────────────────────────────────────────────────────────
# Cheon needs a *prime* group order, so work in the prime-order subgroup:
# 1000002 = 2 * 3 * 166667, and g^6 generates the subgroup of order 166667.
# Then d = 2 divides q - 1 = 166666 = 2 * 83333.
SUBG=$("$CA" group exp "${ZP[@]}" --elem 858101 --k 6 | sed 's/.*"\([0-9]*\)".*/\1/')
want '"status":"ok"' cheon --group zp --p 1000003 --order 166667 --g "$SUBG" --d 2 --alpha 4242
cheon_tmp=$(mktemp -d)
CHEON=(cheon --group zp --p 1000003 --order 166667 --g "$SUBG" --d 2 --alpha 4242 \
  --state-dir "$cheon_tmp/local" --checkpoint-every 1 --progress-every 1)
want_no '"status":"limit reached"' "${CHEON[@]}" --max-exps 3
checks=$((checks + 1))
if [ ! -s "$cheon_tmp/local/cheon.ckpt" ] || \
   ! grep -q '"phase":"first-baby"' "$cheon_tmp/local/cheon.ckpt.progress.json"; then
  printf 'FAIL: Cheon partial checkpoint or phase progress missing\n' >&2
  fail=$((fail + 1))
fi
want '"alpha":4242' "${CHEON[@]}" --max-exps 1000 --resume
checks=$((checks + 1))
if ! grep -q '"phase":"complete"' "$cheon_tmp/local/cheon.ckpt.progress.json" || \
   ! grep -q '"alpha":4242' "$cheon_tmp/local/result.json" || \
   ! grep -q '"g_alpha":"' "$cheon_tmp/local/result.json"; then
  printf 'FAIL: Cheon resume did not finish and persist the result\n' >&2
  fail=$((fail + 1))
fi
want_bad 'run manifest does not match' cheon --group zp --p 1000003 --order 166667 \
  --g "$SUBG" --d 2 --alpha 4243 --state-dir "$cheon_tmp/local" --resume
mkdir "$cheon_tmp/bin" "$cheon_tmp/remote"
cat >"$cheon_tmp/bin/aws" <<'AWS'
#!/usr/bin/env bash
set -euo pipefail
src=$3 dst=$4
if [[ $src == s3://* ]]; then src=$CA_TEST_S3_ROOT; fi
if [[ $dst == s3://* ]]; then dst=$CA_TEST_S3_ROOT; fi
mkdir -p "$dst"
if compgen -G "$src/*" >/dev/null; then cp "$src/"* "$dst/"; fi
AWS
chmod +x "$cheon_tmp/bin/aws"
CHEON_S3=(cheon --group zp --p 1000003 --order 166667 --g "$SUBG" --d 2 --alpha 4242 \
  --state-dir "$cheon_tmp/s3-local" --s3-uri s3://test/cheon --sync-every 1)
PATH="$cheon_tmp/bin:$PATH" CA_TEST_S3_ROOT="$cheon_tmp/remote" \
  want_no '"status":"limit reached"' "${CHEON_S3[@]}" --max-exps 3
rm -rf "$cheon_tmp/s3-local"
PATH="$cheon_tmp/bin:$PATH" CA_TEST_S3_ROOT="$cheon_tmp/remote" \
  want '"alpha":4242' "${CHEON_S3[@]}" --max-exps 1000 --resume
checks=$((checks + 1))
if [ ! -s "$cheon_tmp/remote/cheon.ckpt" ] || \
   ! grep -q '"alpha":4242' "$cheon_tmp/remote/result.json"; then
  printf 'FAIL: Cheon S3 mirror or restore artifacts missing\n' >&2
  fail=$((fail + 1))
fi
cp "$cheon_tmp/remote/cheon.ckpt" "$cheon_tmp/remote-good.ckpt"
printf X >>"$cheon_tmp/s3-local/cheon.ckpt"
PATH="$cheon_tmp/bin:$PATH" CA_TEST_S3_ROOT="$cheon_tmp/remote" \
  want_bad 'Cheon checkpoint failed validation before S3 sync' "${CHEON_S3[@]}" \
  --max-exps 1000 --resume
checks=$((checks + 1))
if ! cmp -s "$cheon_tmp/remote/cheon.ckpt" "$cheon_tmp/remote-good.ckpt"; then
  printf 'FAIL: invalid local Cheon checkpoint replaced the S3 copy\n' >&2
  fail=$((fail + 1))
fi
rm -rf "$cheon_tmp"

# ── the distributed protocol ────────────────────────────────────────────────
# The job document is the whole agreement between participants, so the smoke
# test covers minting one, refusing a malformed one, and walking it: `work`
# with no --coordinator walks alone, which is the same code path a fleet
# runs, minus the socket.
H=$("$CA" group exp "${ZP[@]}" --elem 858101 --k 123456 | sed 's/.*"\([0-9]*\)".*/\1/')
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

want '"job_id"' coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 \
  --seed 42 --out "$tmp/job.txt"
want_fail coord-job "${ZP[@]}" --g 858101            # --h is required
want_fail coord-job "${ZP[@]}" --g 858101 --h "$H" --r 2   # r must be in [4, 4096]

# The same job twice is the same id: that is what lets two agents agree
# without exchanging anything.
first=$("$CA" coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 --seed 42)
second=$("$CA" coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 --seed 42)
checks=$((checks + 1))
if [ "$first" != "$second" ]; then
  printf 'FAIL: the same job minted two different ids\n' >&2
  fail=$((fail + 1))
fi

want '"x":123456' work --job "$tmp/job.txt" --node solo --threads 2 --max-seconds 60

# Sharding: the count rides in the document, so it changes the id, and a
# document that declares it says so.
sharded=$("$CA" coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 --seed 42 --shards 4)
checks=$((checks + 1))
if [ "$sharded" = "$first" ]; then
  printf 'FAIL: --shards did not change the job id\n' >&2
  fail=$((fail + 1))
fi
want 'sh=4' coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 --seed 42 --shards 4
want_fail coord-job "${ZP[@]}" --g 858101 --h "$H" --shards 0
want_fail coord-job "${ZP[@]}" --g 858101 --h "$H" --shards 99999
# A sharded job needs one coordinator URL per shard, in shard order; one
# URL for four shards is refused rather than silently under-split.
"$CA" coord-job "${ZP[@]}" --g 858101 --h "$H" --dp-bits 4 --unit-size 64 --seed 42 \
    --shards 4 --out "$tmp/sharded.txt" >/dev/null 2>&1
want_fail work --job "$tmp/sharded.txt" --coordinator http://127.0.0.1:1 --max-seconds 1
# And with no coordinator at all it still walks: sharding is about where
# points are sent, not whether they are found.
want '"shards":4' work --job "$tmp/sharded.txt" --node solo --threads 2 --max-seconds 60
want_fail coord-status --coordinator http://127.0.0.1:1   # nothing is listening

# ── sibling Rust CLI dispatch ───────────────────────────────────────────────
# Direct argv forwarding keeps whitespace and shell metacharacters literal,
# and the child exit status must reach the caller unchanged.
cat >"$tmp/forwarded" <<'SH'
#!/bin/sh
printf '%s\n' "$@"
exit 7
SH
chmod +x "$tmp/forwarded"
checks=$((checks + 1))
rc=0
out=$(CA_CRYPTO_BIN="$tmp/forwarded" "$CA" crypto 'two words' '$HOME') || rc=$?
if [ "$rc" -ne 7 ] || [ "$out" != $'two words\n$HOME' ]; then
  printf 'FAIL: crypto delegation changed argv or exit status (rc=%d, out=%s)\n' "$rc" "$out" >&2
  fail=$((fail + 1))
fi
export CA_ICX_BIN=/bin/echo
want 'solve-prime --p 271' icx solve-prime --p 271
unset CA_ICX_BIN
export CA_CRAX_BIN=/bin/echo
want 'hash --algorithm sha256' crax hash --algorithm sha256
unset CA_CRAX_BIN
export CA_ISOGENY_WALK_BIN=/bin/echo
want 'verify --dir example' isogeny-walk verify --dir example
unset CA_ISOGENY_WALK_BIN
checks=$((checks + 1))
rc=0
CA_CRYPTO_BIN="$tmp/missing" "$CA" crypto --help >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 127 ]; then
  printf 'FAIL: missing delegated binary returned %d, expected 127\n' "$rc" >&2
  fail=$((fail + 1))
fi

# ── usage and unknown commands ──────────────────────────────────────────────
want_fail
want_fail not-a-command

printf '%d checks, %d failures\n' "$checks" "$fail"
[ "$fail" -eq 0 ]
