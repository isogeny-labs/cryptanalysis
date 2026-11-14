# Blind arithmetic review: GLV cap 128 selector

Scope: This review uses only the definitions in the assigned prompt. It does not assess any implementation, Lean statement, proof artifact, build, experiment, or historical source. All variables below are natural numbers. Define `q = s / (12*lg)` with natural-number floor division, and define `old(s,lg) = loopCap(32,q)`. For claim 19 only, interpret “historical divisor48 cap32 select” as `hist48(s,lg) = loopCap(32, s / (48*lg))`.

## Derived rule

A step doubles `r` exactly when both `b >= 2*r` and `cap >= 2*r`. Starting at 8, the four possible thresholds are 16, 32, 64, and 128. Thus, for either allowed cap, the loop reaches the largest member of `8,16,32,64,128` that is at most both `b` and `cap`, except that its initial value remains 8 when `b < 8`. Equivalently, its value is the threshold table stated in the prompt.

## Verdict on the 19 supplied claims

| # | Claim, as parsed from the prompt | Verdict | Reason |
|---:|---|---|---|
| 1 | `lg < 40 -> capFor(lg) = 32` | Valid | First definition branch. |
| 2 | `lg >= 40 -> capFor(lg) = 128` | Valid | Complementary branch for naturals. |
| 3 | `loopCap(32,b) = tableSize(b)` | Valid | The only reachable doublings are at 16 and 32. |
| 4 | `loopCap(128,b) = tableSize128(b)` | Valid | The four reachable doublings are at 16, 32, 64, and 128. |
| 5 | The cap-32 loop equals its two-step result | Valid | After two steps it is at 8, 16, or 32; another step cannot change it. |
| 6 | A fifth step fixes `loopCap(32,b)` | Valid | It is already fixed after at most two steps. |
| 7 | A fifth step fixes `loopCap(128,b)` | Valid | If the fourth step did not double, `b` is below the next threshold; if it did, the result is the cap. |
| 8 | `tableSize128` has the stated five cases | Valid | Values are 8 for `b<16`, 16 for `16<=b<32`, 32 for `32<=b<64`, 64 for `64<=b<128`, and 128 for `b>=128`. |
| 9 | `tableSize128` is monotone in `b` | Valid, non-strict | Its successive case values increase at thresholds and are constant within cases. |
| 10 | `tableSize(b) <= tableSize128(b)` | Valid | The values agree below 64; at 64 and above the former is 32 and the latter is at least 64. |
| 11 | `b<64 -> tableSize(b) = tableSize128(b)` | Valid | Both have only the 16 and 32 thresholds in this range. The bound is sharp: at 64 the values are 32 and 64. |
| 12 | `lg<40 -> select(s,lg) = old(s,lg)` | Valid | Both use cap 32 and the same quotient. |
| 13 | `lg>=40 -> select(s,lg) = tableSize128(q)` | Valid | The cap is 128 and claim 4 applies. |
| 14 | `8 <= select(s,lg)` | Valid | Every step starts at 8 and either preserves or doubles it. |
| 15 | `select(s,lg) <= capFor(lg)` | Valid | Initial 8 is below either cap, and each doubling checks its cap bound. |
| 16 | `select` has the appropriate cases according to `lg` | Valid | For `lg<40`, apply the three cases of `tableSize(q)`; for `lg>=40`, apply the five cases of `tableSize128(q)`. At `lg=0`, `q=0` and the value is 8. |
| 17 | `select(s,lg)` is monotone in `s` for fixed `lg` | Valid, non-strict | For positive `lg`, division by the fixed positive `12*lg` is monotone; the threshold tables are monotone. For `lg=0`, the quotient and selector are constant. |
| 18 | `old(s,lg) <= select(s,lg)` for all `s,lg` | Valid | Equality holds below 40; above 39, claim 10 applies to their shared quotient. |
| 19 | `hist48(s,lg) <= select(s,lg)` when `lg>0` | Valid under the stated interpretation | Since `48*lg >= 12*lg > 0`, `s/(48*lg) <= s/(12*lg)`. The cap-32 table is monotone, and claim 18 then gives the result. |

## Boundary controls and adverse readings

| Control | `tableSize(b)` | `tableSize128(b)` |
|---:|---:|---:|
| 15 | 8 | 8 |
| 16 | 16 | 16 |
| 31 | 16 | 16 |
| 32 | 32 | 32 |
| 63 | 32 | 32 |
| 64 | 32 | 64 |
| 127 | 32 | 64 |
| 128 | 32 | 128 |

The `lg` branch changes between 39 and 40. It does not imply monotonicity in `lg`, because the divisor changes too: at `s=7488`, `select(s,39)=16` while `select(s,40)=8`; at `s=30720`, the values are 32 and 64, respectively.

Any strict version of claims 9, 10, 17, or 18 is false. For example, both tables equal 8 at `b=0`; for fixed positive `lg`, `s=0` and `s=1` both select 8; and old and current selectors agree for every `lg<40`. A proposed equality through `b<=64` is false at 64. A claim that the new cap always attains 128 is false whenever its quotient is below 128.

Lean-style natural division is total at zero: `s/0 = 0`. Hence `select(s,0)=8` for every `s`; no positive-denominator cancellation or quotient comparison may be used at `lg=0`. Claim 19 was supplied with `lg>0`, which makes the denominator comparison valid. Under the explicit `hist48` definition above, its inequality also holds at zero because both quotients are zero, but that extension requires a separate zero-case argument. The exact historical definition was not supplied; claim 19's verdict is conditional on the interpretation stated here.
