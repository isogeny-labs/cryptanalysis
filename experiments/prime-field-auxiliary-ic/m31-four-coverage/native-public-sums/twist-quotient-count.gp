p = 2^31 - 1;
left = ellcard(ellinit([2,14], p));
right = ellcard(ellinit([2,-14], p));
if (left%2 != 1 || right%2 != 1 || left+right != 2*p+2, error("Unexpected root or trace"));
trace1 = ellap(ellinit([0,4,0,4,-196], p));
\\ Reciprocal cubic has coefficients (-196,4,4,1) in descending order.
\\ For leading coefficient a, use (X,Y) = (a*x,a*y) to make it monic.
trace2 = ellap(ellinit([0,4,0,-784,196^2], p));
correlation = -1 - trace1 - trace2;
print([(left-1)/2, (right-1)/2, (p+correlation)/4]);
