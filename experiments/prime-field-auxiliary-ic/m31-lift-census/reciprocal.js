// Run with node reciprocal.js. The bitmap stores strictly nonzero squares.
"use strict";
const assert = require("node:assert/strict");
const p = 2147483647;
const squares = new Uint32Array(Math.ceil(p / 32));
function add(a, b) {
    const sum = a + b;
    return sum >= p ? sum - p : sum;
}
function isNonzeroSquare(x) {
    return (squares[x >>> 5] >>> (x & 31)) & 1;
}
let square = 0;
for (let i = 1; i <= (p - 1) / 2; ++i) {
    square = add(square, 2 * i - 1);
    squares[square >>> 5] |= 1 << (square & 31);
}
let pairs = 0, mixed = 0, zeros = 0;
// F(t) = 14t^3 + 2t^2 - 14t + 197 and its forward differences.
let product = 197, delta = 2, secondDelta = 88;
for (let t = 0; t < p; ++t) {
    if (isNonzeroSquare(t) && t !== 2 && t !== p - 2 &&
        !isNonzeroSquare(add(t, p - 2)) && !isNonzeroSquare(add(t, 2))) {
        ++pairs;
        if (product === 0) ++zeros;
        else if (!isNonzeroSquare(product)) ++mixed;
    }
    product = add(product, delta);
    delta = add(delta, secondDelta);
    secondDelta = add(secondDelta, 84);
}
assert.deepEqual([product, delta, secondDelta], [197, 2, 88]);
assert.equal(pairs, 2 ** 28);
assert.equal(zeros, 0);
console.log(JSON.stringify({ p, pairs, mixed, zeros }));
