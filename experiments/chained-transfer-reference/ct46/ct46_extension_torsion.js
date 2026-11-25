'use strict';
// CT46 independent extension-field matrix enumeration [pcc:unverified].
const p=101;
function mod(a,m){return ((a%m)+m)%m;}
function F(t,m){return [0,mod(-p,m),1,mod(t,m)];}
function product(x,y,m){const [a,b,c,d]=x,[e,f,g,h]=y;
 return [mod(a*e+b*g,m),mod(a*f+b*h,m),mod(c*e+d*g,m),mod(c*f+d*h,m)];}
function mpow(a,k,m){let z=[1,0,0,1];for(;k>0;k=Math.floor(k/2)){
 if(k%2)z=product(z,a,m);a=product(a,a,m);}return z;}
function determinant(a,m){return mod(a[0]*a[3]-a[1]*a[2],m);}
function commute(x,y,m){for(let i=0;i<4;i++)if(x[i]!==y[i])return false;return true;}
function census(m,k){const e=mpow(F(-7,m),k,m),f=mpow(F(-11,m),k,m);
 let count=0,unit=0,anti=0;
 for(let a=0;a<m;a++)for(let b=0;b<m;b++)for(let c=0;c<m;c++)for(let d=0;d<m;d++){
  const x=[a,b,c,d];if(!commute(product(x,e,m),product(f,x,m),m))continue;
  count++;const dt=determinant(x,m);if(dt&1)unit++;if(dt===m-1)anti++;
 }
 return [count,unit,anti];
}
for(const [m,k,t,u,a] of [[8,1,16,0,0],[8,2,64,48,12],[16,1,16,0,0],
  [16,2,64,0,0],[16,3,1024,0,0],[16,4,256,192,24]]){
 const got=census(m,k);if(got[0]!==t||got[1]!==u||got[2]!==a)
  throw new Error(`wrong census ${m}/${k}: ${got}`);
}
// A completely separate direct matrix equality test of frozen certificates.
for(const [m,k,x] of [[8,2,[7,6,2,5]],[16,4,[9,2,6,3]],
 [32,8,[30,13,27,1]],[64,16,[21,43,5,62]]]){
 const a=mpow(F(-7,m),k,m),b=mpow(F(-11,m),k,m);
 if(!commute(product(x,a,m),product(b,x,m),m)||determinant(x,m)!==m-1)
  throw new Error(`bad witness ${m}/${k}`);
 // Negative control: same witness must not silently be promoted to k=1.
 if(k>1&&commute(product(x,F(-7,m),m),product(F(-11,m),x,m)))
  throw new Error('wrong-field witness accepted');
 console.log(`mod=${m} extension=${k} independent witness PASS [pcc:unverified]`);
}
console.log('CT46 JS PASS: exhaustive 8/16 and independent frozen higher-lift checks [pcc:unverified]');
