// CT42: prime-field sextic irreducibility and geometric J[2] Frobenius.
// Independent of producer Cantor/Richelot/elliptic code; [pcc:unverified].
'use strict';
const p=101, need=(ok,msg)=>{if(!ok)throw Error(msg)}, mod=x=>(x%p+p)%p;
const curves={T0:[31,75,74,54,71,55,1],T1:[95,26,19,27,94,91,1],T2:[95,93,43,39,92,17,1],
  control33:[37,75,74,54,71,55,1],control24:[31,79,74,54,71,55,1]};
const norm=a=>{a=a.map(mod);while(a.length&&!a.at(-1))a.pop();return a};
const sub=(a,b)=>norm(Array.from({length:Math.max(a.length,b.length)},(_,i)=>(a[i]||0)-(b[i]||0)));
const mul=(a,b)=>{if(!a.length||!b.length)return [];const c=Array(a.length+b.length-1).fill(0);
  a.forEach((v,i)=>b.forEach((w,j)=>c[i+j]=mod(c[i+j]+v*w)));return norm(c)};
const pow=(a,n)=>{let r=1;for(;n;n=Math.floor(n/2),a=mod(a*a))if(n%2)r=mod(r*a);return r};
const rem=(aa,bb)=>{let a=norm([...aa]),b=norm([...bb]);need(b.length,'zero polynomial');const inv=pow(b.at(-1),p-2);
  while(a.length>=b.length){const s=a.length-b.length,v=mod(a.at(-1)*inv);
    b.forEach((w,i)=>a[s+i]=mod(a[s+i]-v*w));a=norm(a)}return a};
const gcd=(aa,bb)=>{let a=norm([...aa]),b=norm([...bb]);while(b.length)[a,b]=[b,rem(a,b)];
  return a.length?norm(a.map(x=>mod(x*pow(a.at(-1),p-2)))):[]};
const powmod=(aa,n,f)=>{let a=aa,r=[1];for(;n;n=Math.floor(n/2),a=rem(mul(a,a),f))
  if(n%2)r=rem(mul(r,a),f);return r};
const sig=f=>{need(f.length===7&&f[6]===1,'nonmonic sextic');
  need(JSON.stringify(gcd(f,norm(f.slice(1).map((v,i)=>v*(i+1)))))==='[1]','singular');
  let a=[0,1];return Array.from({length:6},()=>{a=powmod(a,p,f);return gcd(f,sub(a,[0,1])).length-1})};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
for(const [n,f] of Object.entries(curves)){
  const found=sig(f), expected=n==='control33'?[0,0,6,0,0,6]:n==='control24'?[0,2,0,6,0,2]:[0,0,0,0,0,6];
  need(same(found,expected),`factor cycle ${n}`);console.log(`${n}: ${found.join(',')}`);
}
// J[2] = even 6-subsets / complement, each 6-bit word is a subset.
const b=Array.from({length:4},(_,i)=>(1<<i)^(1<<5));
const rotate=v=>((v<<1)|(v>>5))&63;
const coordinates=v=>{need((v.toString(2).replace(/0/g,'').length%2)===0,'odd subset');
  for(let m=0;m<16;m++){let w=0;for(let i=0;i<4;i++)if(m&(1<<i))w^=b[i];
    if(v===w||v===(w^63))return m}throw Error('bad quotient vector')};
const F=b.map(v=>coordinates(rotate(v))), I=[1,2,4,8];
const apply=(M,v)=>M.reduce((acc,c,i)=>(v&(1<<i))?acc^c:acc,0);
const compose=(A,B)=>B.map(v=>apply(A,v));
const power=(M,k)=>{let R=I;while(k){if(k%2)R=compose(M,R);M=compose(M,M);k=Math.floor(k/2)}return R};
const rank=columns=>{let r=0,a=[...columns];for(let bit=0;bit<4;bit++){
  const pos=a.findIndex((v,i)=>i>=r&&(v&(1<<bit)));if(pos<0)continue;
  [a[r],a[pos]]=[a[pos],a[r]];for(let j=0;j<4;j++)if(j!==r&&(a[j]&(1<<bit)))a[j]^=a[r];r++}return r};
const F3=power(F,3);need(same(power(F,6),I),'F6');
const r3=rank(F3.map((v,i)=>v^I[i])),r1=rank(F.map((v,i)=>v^I[i]));
need(r3===2&&r1===4,'J[2] quotient Jordan controls');
for(const t of [-7,-11])need((t*t-101)%4===0&&(1-101*t)%4===0,'component F3+I divisibility');
console.log(`J[2] F columns ${F}; rank(F^3-I) ${r3}; rank(F-I) ${r1}; F^6=I`);
console.log('If CT39 Weil factorization holds, 2-adic glue quotient has exponent 4 and order 16.');
console.log('PASS [pcc:unverified] (no Picard/polarization or native map certificate)');
