'use strict';
const fs=require('fs');
function buildPdf(){
  const pg1=[
    [20,48,747,"CT45: exact finite-level cross-factor Hom"],
    [11,48,721,"E109 / E113 over F101 | 2026-11-12 | [pcc:unverified]"],
    [13,48,673,"Theorem in Frobenius companion bases"],
    [11,48,642,"For m coprime to 101:  C(t) = [[0,-101],[1,t]] mod m."],
    [11,48,618,"Every X satisfying X C(-7) = C(-11) X has exactly the form:"],
    [11,63,590,"X(a,c) = [[a,-101c],[c,a-11c]], with 4a=4c=0 (mod m)."],
    [11,48,558,"Thus 4X=0. Odd levels have no nonzero cross-factor maps."],
    [11,48,531,"For m=2^k, there are exactly 16 intertwiners at all k >= 2."],
    [13,48,482,"Independent check results"],
    [11,60,447,"Modulus       All maps          Units           Main observation"],
    [11,60,420,"2                  4                      3               three 2-torsion maps"],
    [11,60,394,"4                  16                    12               six Weil anti-isometries"],
    [11,60,368,"8                  16                    0               every entry even"],
    [11,60,342,"16                16                    0               every entry divisible by 4"],
    [11,60,316,"32/256         16 each            0               formula-checked; no brute claim"],
    [13,48,268,"Interpretation and scope"],
    [11,48,241,"No level-four anti-isometry lifts to a full equivariant 8-torsion isomorphism."],
    [11,48,217,"Finite-level Galois maps need not be geometric elliptic homomorphisms."],
    [11,48,193,"No actual genus-two kernel, PCC signature or DLP speedup is established."],
    [10,48,108,"Controls: independent Python/JS exhaustive mod 2/4/8/16; positive trace -15."],
    [9,48,49,"Sources: Bruin-Doerksen (2011), crypto PR #3877, cryptanalysis PR #1502."]
  ];
  const pg2=[
    [20,48,738,"The 4-torsion lift barrier"],
    [14,84,565,"Level 4"],[14,263,565,"Level 8"],[14,445,565,"Level 16"],
    [12,76,515,"12 invertible"],[12,255,515,"0 invertible"],[12,437,515,"0 invertible"],
    [10,76,483,"6 anti-isometries"],[10,255,483,"all entries even"],[10,437,483,"all entries / 4"],
    [13,49,388,"Every Frobenius intertwiner is annihilated by 4."],
    [11,49,349,"Proof: expand X C(-7)=C(-11) X. The trace gap is four."],
    [11,49,322,"The resulting two parameters a,c satisfy 4a=4c=0 modulo m."],
    [11,49,295,"Therefore the only compatible 2-adic Tate-module map is zero."],
    [11,49,251,"Positive mutant: trace -15 admits 48 invertible maps mod 8."],
    [11,49,214,"Next: compare the actual native U graph, degree-7 A/B and CT44 dual"],
    [11,49,190,"using independent Cantor and Weil tests. Full solver costs still pending."],
    [10,49,112,"Reproduce: python3 -B .../ct45_cross_torsion.py"],
    [10,49,90, "                 node .../ct45_cross_torsion.js"],
    [9,49,49,"[pcc:unverified] | No paid compute."]
  ];
  const quote=s=>"("+String(s).replace(/\\/g,"\\\\").replace(/\(/g,"\\(").replace(/\)/g,"\\)")+")";
  const makeStream=(lines,diagram)=>{
    let s="";
    if(diagram) s+="0.89 0.95 0.91 rg 55 455 160 155 re f 0.99 0.93 0.86 rg 233 455 160 155 re f 0.98 0.89 0.91 rg 413 455 160 155 re f 0 0 0 rg ";
    for(const [size,x,y,z] of lines) s+=`BT /F1 ${size} Tf ${x} ${y} Td ${quote(z)} Tj ET\n`;
    return s;
  };
  const streams=[makeStream(pg1,false),makeStream(pg2,true)];
  const objects=[
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    `<< /Length ${streams[0].length} >>\nstream\n${streams[0]}endstream`,
    `<< /Length ${streams[1].length} >>\nstream\n${streams[1]}endstream`
  ];
  let out="%PDF-1.4\n", offsets=[0];
  for(let i=0;i<objects.length;i++){offsets.push(out.length);out+=`${i+1} 0 obj\n${objects[i]}\nendobj\n`;}
  const start=out.length;out+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`;
  for(let i=1;i<offsets.length;i++)out+=String(offsets[i]).padStart(10,"0")+" 00000 n \n";
  out+=`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF\n`;
  return out;
}
const dest=process.argv[2]||__dirname+'/CT45_Report.pdf';
fs.writeFileSync(dest,buildPdf(),'ascii');
