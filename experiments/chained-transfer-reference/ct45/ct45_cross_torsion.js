'use strict';
// CT45 independent raw-matrix equation oracle [pcc:unverified].
const p=101, tA=-7, tB=-11;
function mod(x,n){return ((x%n)+n)%n;}
function F(t,n){return [[0,mod(-p,n)],[1,mod(t,n)]];}
function mul(x,y,n){return [
 [mod(x[0][0]*y[0][0]+x[0][1]*y[1][0],n),mod(x[0][0]*y[0][1]+x[0][1]*y[1][1],n)],
 [mod(x[1][0]*y[0][0]+x[1][1]*y[1][0],n),mod(x[1][0]*y[0][1]+x[1][1]*y[1][1],n)]];}
function det(x,n){return mod(x[0][0]*x[1][1]-x[0][1]*x[1][0],n);}
function eq(x,y){return JSON.stringify(x)===JSON.stringify(y);}
function gcd(a,b){while(b){const r=a%b;a=b;b=r;}return a;}
function count(n,t=tB){let total=0,units=0,anti=0;const fa=F(tA,n),fb=F(t,n);
  for(let a=0;a<n;a++)for(let b=0;b<n;b++)for(let c=0;c<n;c++)for(let d=0;d<n;d++){
    const x=[[a,b],[c,d]];
    if(!eq(mul(x,fa,n),mul(fb,x,n)))continue;
    ++total;
    if(t===tB && [a,b,c,d].some(z=>mod(4*z,n)!==0))throw Error('4X != 0');
    if(t===tB && n>=8 && ((a|b|c|d)&1))throw Error('nonzero mod2 reduction');
    if(gcd(det(x,n),n)===1){++units;if(n===4&&det(x,n)===3)++anti;}
  }
  return {total,units,anti};
}
for(const [n,all,unit] of [[2,4,3],[4,16,12],[8,16,0],[16,16,0]]){
  const r=count(n);
  if(r.total!==all||r.units!==unit||(n===4&&r.anti!==6))
    throw Error('wrong census: '+n+' '+JSON.stringify(r));
  console.log(n+': '+r.total+' intertwiners; '+r.units+' invertible [pcc:unverified]');
}
const altered=count(8,-15);
if(altered.total!==64||altered.units!==48)throw Error('wrong-trace control');
for(const n of [3,5,7])if(count(n).total!==1)throw Error('odd control '+n);
console.log('CT45 JS PASS: exhaustive and mutated controls [pcc:unverified]');
