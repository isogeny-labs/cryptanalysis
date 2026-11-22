// Run with node census.js. The square-residue bitmap uses 256 MiB.
"use strict";
const assert = require("node:assert/strict");
const p = 2147483647;
const squares = new Uint32Array(Math.ceil(p / 32));
function add(a, b) {
    const sum = a + b;
    return sum >= p ? sum - p : sum;
}
function isSquare(x) {
    return (squares[x >>> 5] >>> (x & 31)) & 1;
}

// Include zero. The other half of the field repeats the same squares.
let square = 0;
let increment = 1;
for (let i = 0; i <= (p - 1) / 2; ++i) {
    squares[square >>> 5] |= 1 << (square & 31);
    square = add(square, increment);
    increment = add(increment, 2);
}

let eligible = 0, liftable = 0, intersection = 0, cubicZeros = 0;
let squarePlusOne = 1, squareDelta = 1;
let cubic = 14, cubicDelta = 3, cubicSecondDelta = 6;
for (let x = 0; x < p; ++x) {
    const lift = isSquare(cubic);
    liftable += lift;
    cubicZeros += Number(cubic === 0);
    if (!isSquare(x) && !isSquare(squarePlusOne)) {
        eligible++;
        intersection += lift;
    }
    squarePlusOne = add(squarePlusOne, squareDelta);
    squareDelta = add(squareDelta, 2);
    cubic = add(cubic, cubicDelta);
    cubicDelta = add(cubicDelta, cubicSecondDelta);
    cubicSecondDelta = add(cubicSecondDelta, 6);
}
assert.equal(eligible, 2 ** 29);
assert.equal(liftable, (2147505293 - 1) / 2);
assert.equal(cubicZeros, 0);
assert.equal(squarePlusOne, 1);
assert.equal(cubic, 14);
const rootSets = eligible / 32;
console.log(JSON.stringify({ p, eligible, liftable, intersection, rootSets,
    meanLiftsPerSet: intersection / rootSets }, null, 2));
