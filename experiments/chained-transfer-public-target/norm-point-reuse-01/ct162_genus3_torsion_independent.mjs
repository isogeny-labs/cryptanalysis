// CT162 alternate Node.js GF(2)-array calculation / Weierstrass-class check.
// No import from Python checker. Necessary condition, [pcc:unverified].
import fs from 'node:fs';
import crypto from 'node:crypto';
const dataPath=new URL('./CT160_FULL_CENSUS.json',import.meta.url);
const data=fs.readFileSync(dataPath);
const expectedSHA='58af5c02d3a5afc722e1662e2fb5ade0534e65f824a29c97abc51dab827d08c8';
if(crypto.createHash('sha256').update(data).digest('hex')!==expectedSHA)throw Error('input sha mismatch');
const input=JSON.parse(data.toString('utf8'));
for(const side of ['actual_fixed_nu12_source','actual_fixed_nu12_target']){
  const d=input[side];
  if(d.zeros!==3||d.order!==11086844||1+d.zeros+2*d.nonzero_squares!==d.order)throw Error('bad source');
}
if(input.field_cardinality!==223**3||input.accepted!==true)throw Error('invalid record');
function parts(total,min=1){
  if(total===0)return [[]];
  const out=[];
  for(let i=min;i<=total;i++)for(const rest of parts(total-i,i))out.push([i,...rest]);
  return out;
}
function mul(a,b){const c=Array(a.length+b.length-1).fill(0);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)c[i+j]^=a[i]&b[j];return c;}
function divideByXPlus1Sq(a){
  let v=a.slice();const quotient=Array(v.length-2).fill(0);
  for(let j=v.length-1;j>=2;j--){if(v[j]){
    quotient[j-2]=1;
    v[j]^=1;v[j-2]^=1;
  }}
  if(v.some(x=>x!==0))throw Error('nonexact quotient');
  return quotient;
}
function poly(d){
  let coeffs=[1];
  for(const l of d){let q=Array(l+1).fill(0);q[0]=1;q[l]=1;coeffs=mul(coeffs,q);}
  return divideByXPlus1Sq(coeffs);
}
function fixedCount(d){
  const move=[];let k=0;
  for(const l of d){for(let j=0;j<l;j++)move[k+j]=k+(j+1)%l;k+=l;}
  let count=0,seen=0;
  for(let mask=0;mask<256;mask++){
    if(mask&128||((mask.toString(2).replace(/0/g,'').length)%2))continue;
    seen++;
    let rotated=0;
    for(let j=0;j<8;j++)if(mask&(1<<j))rotated^=(1<<move[j]);
    if(rotated===mask||rotated===(mask^255))count++;
  }
  if(seen!==64)throw Error('two torsion quotient dimension');
  return count;
}
const target=[1,0,0,0,0,0,1];
const accepted=parts(8).filter(d=>JSON.stringify(poly(d))===JSON.stringify(target)).map(d=>({d,rationalJ2:fixedCount(d)}));
const expected=[{d:[1,1,3,3],rationalJ2:4},{d:[1,1,6],rationalJ2:2},{d:[2,3,3],rationalJ2:2},{d:[2,6],rationalJ2:4}];
if(JSON.stringify(accepted)!==JSON.stringify(expected))throw Error('unexpected candidate');
console.log(JSON.stringify({language:'node-independent',partitions_tested:parts(8).length,accepted,odd_degree_compatible:accepted.filter(x=>x.rationalJ2===4).map(x=>x.d)}));
