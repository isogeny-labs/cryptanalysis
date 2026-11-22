p = 2^31 - 1;
aux = ellinit([1, 0], p);
target = ellinit([2, 14], p);
G = [Mod(3, p), Mod(615668188, p)];
K = ellmul(aux, G, 2^26);
setrand(24117);
indices = Set(vector(8300, i, random(2^24)));
histogram = vector(33);
for(i = 1, #indices, \
  R = ellmul(aux, G, 2*indices[i]+1); count = 0; \
  for(k = 1, 32, count += (#ellordinate(target, R[1]) > 0); \
      if(k < 32, R = elladd(aux, R, K))); \
  histogram[count+1]++);
print([#indices, histogram, sum(i=18,33,histogram[i])]);
