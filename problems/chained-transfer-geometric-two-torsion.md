# Actual q223 geometric two-torsion and a second nondual Jacobian map

- **Status:** open
- **Kind:** implementation gap and partial formalization
- **Affected work:** Chained ECDLP Transfers, crypto PR3877 and cryptanalysis
  PR1523; [two-primary derivation](../experiments/chained-transfer-public-target/two-primary/DERIVATION-01.md)
- **Next action owner:** current research session / next resuming session
- **Last updated:** 2026-11-13

## Problem

The actual prime-field genus3 Jacobian has no second implemented nondual
isogeny in this continuation: its geometric two-torsion coordinates,
Frobenius action and suitable kernel/codomain construction remain missing.

The exact fixed case is N4 q223/seed1, K=F223[z]/(z³−3), ell2773073,
order11092292. The completed Phi/Norm pair has both compositions[2]. Going
back through the same dual pair is insufficient to establish a useful new
chain or computational advantage. [pcc:unverified]

## Evidence and uncertainty

- **Observed:** native02/510d03 uses original arithmetic and all224 rational
  C point classes, four cofactor classes, all16 sums and64 associative triples.
  Rational Jacobian2-Sylow is C4; source E(K)[2] is C2×C2. Both rational map
  kernels/images have size2, and both compositions pass. All2318 selected
  source hashes remain unchanged. Partial-capture01 is retained in1311d9.
  [pcc:unverified]
- **Derived:** written65f7a4 combines this fixed-point count with the Ciani
  Weil polynomial to derive full geometric J[2] splitting degree6. All four
  faithful partial algebra declarations pass both original Lean gates and
  exact local PCC bindings. Actual geometric/Tate/CH/orbit/field bridges are
  written and remain open in Lean. [pcc:unverified]
- **Missing capability:** the reviewed original plane-quartic Picard engine
  handles admitted prime fields; it has no established F223^6 group interface
  in the checked source catalogc3b30d. Genus-two Richelot and hyperelliptic
  arithmetic do not automatically support this smooth plane quartic.
  [pcc:unverified]
- **Unknown:** actual geometric Frobenius matrix, stable maximal-isotropic
  kernels, explicit nondual codomains, and their total solving cost. The
  characteristic polynomial alone does not justify a semisimple order-three
  action or a stable-kernel count. [pcc:unverified]
- **Limits:** a full torsion field of degree6 does not exclude an F223-rational
  isogeny. Its kernel need only be Frobenius-stable. Missing KB tools and the
  encrypted atlas give no absence or novelty evidence. [pcc:unverified]

## What would unblock it

- [ ] Construct actual geometric J[2] coordinates and Frobenius action over
  the required extension, or an explicit equivalent coordinate kernel descent;
  retain independent field, curve/divisor, torsion and descent checks.
- [ ] Select an actual Frobenius-stable maximal-isotropic kernel distinct
  from the original dual backtrack; compute its codomain and explicit map.
- [ ] Prove the homomorphism and nonzero prime-ell transport, independently [pcc:unverified]
  replay maps/compositions, and complete feasible faithful Lean obligations.

These conditions establish an executable second transfer. A computational
advantage still requires original benchmark admission, complete arithmetic
accounting and matched strongest ECDLP references. [pcc:unverified]

## Next discriminating step

Inspect the original Ciani coordinates, finite-extension arithmetic and
bitangent/divisor machinery. Derive an actual coordinate construction over
F223^6 before writing a kernel census. A first implementation should retain
all28 geometric bitangents or a full rank-six torsion basis, with tangent or
torsion equations and Frobenius closure checked by original field arithmetic.
This is a bounded local correctness development, not an admitted benchmark.
If the chosen API cannot represent the extension or divisor model, preserve
that implementation gap and continue through an explicit extension or
coordinate-descent implementation. A bounded failure does not prove that no
map exists. [pcc:unverified]

## Resolution and history

2026-11-13: native510d03, written65f7a4, exact partial bindings
4e7bfe/cc7273/abcfec/5facfe; two-page reportce9a6d. Unresolved.
[pcc:unverified]

## 2026-11-13T16:04:05.044771+00:00 — actual bitangents, faithful algebra and independent integration

Nativee887a9 passesoneunfilteredtest/all2338selectedhashes unchanged. All28actualWlines(12zero+16generic) haveall5square-restrictioncoefficients/bothchartgradientchecks;28wrongcontactcertificatesreject. ActualFrobeniuscycles1+3+4x6/fixedF,F2,F3,F6=1,1,4,28;16splitand12nonsplitcontactquadratics retained. OriginalRabinFpR(w6-3),Kembeddingz=w2,all15Mooretransportcoefficients pass. ActualL0C0branch0/notclaimedexercised;noJac2basis/Weilpairing/kernelcount/newnondualmap. [pcc:unverified]

FourfaithfulpartialLeanlemmas passbothunchangedoriginal4.35/4.34.1gates andexactoriginalPCCa01f8f/5288a0/6cd1a8/d79edc. Threegeneralringfactor/resultantimplications plusliteral28permutationorder6,actualgeometricbridgesopen. Wholeproofcaptures27da63/49ae01;finalTWO48422bytePDFpagesALLinspected/1efca5. Earlier998cec editable-filenamemetadataerrorretainedimmutable/correctedassets/unchangedPDF. New5a8e82 independentCIplan precedesci_bitangents/separateworkflow;522portableinputs,11positivephasepairs/all4wholeJSON/bothoriginal4gates/4bindings;fouractualadmission/cleanfull/ownCI remainpending. [pcc:unverified]

Parentec826/72paths/e62645 normalpublished0;full25fdf5 all503guards/11phases/fouractualcontrols andallFIVEcurrentCIc225d2SUCCESS/all46native21canonicalPCCdigests match. TENpriorclosedtrees/all20objectsgenuinelypublished f824e8/39084d:13S3(9archives4indices)+7smallGit(1archive6indices),run43453551818/job13198171488913replaysbeforebot32c51/directcbab/exact15paths/all2334then-currenthashes+dirtybytespreserved. Rootfinalmetadatab023747f/53paths/55b40b normalpush0;parser-onlycommandfailureab8cda retained. Guard04released;futurehandoffneedsnewactualcompleteversionincludingbitangents. [pcc:unverified]

Queue: normalpublishthissource+CI522;materialize522+self cleanphysicalGitclones/pinned3dproducer,fouradmissionchecks,launchoriginalfull. ThenindependentfiniteSp6 calculationagainstactual28Frobeniuspermutation andoriginal135Lagrangianenumerator beforeinferringstablekernelcount;actualkernel/divisor/codomainconstructionremainsdownstream. Newtwo-primaryfull/CI/bitangentrawtreesneedfuturegenuinewholedatahandoff. Originalbenchmarkcheckpoint/livebudget/capacity/completecost/strongestrefs andmain/globalfixture/fullformal/vault/KB gapsremain. Nextglobalroutine17:45UTCunlessmaterialsignal. Continueaftereachrung. [pcc:unverified]

## 2026-11-13T17:05:31.707650+00:00 — complete finite kernel census and fixed-degree obstruction

Nativec88589 oneunfiltered/all2361guards0 enumeratesALL1451520distinctSp6matrices/all135certifiedLagrangians/all4096basis-pairings;actualoddcycles1+3+4x6 and2fixedvectorsselect120960actions,eachONEstablekernel. ALLmatrixrecordsretained13063688bytebinary/hash. Readonly907dfc oneunfiltered/all2366guardsincludingbinary0 usesdifferentGaussianrank/truth-tablepowers/commutant route;allrows/predicatecountbytesmatch,centralizer12,classcard120960. OriginalS8representative1pair1any/identity135/transvection15controls. [pcc:unverified]

Written c2270b auditscanonicalCianiNorm/Phi duality/both[2]/degree8/N*lambdaA=2lambdaJ,maxisotropickerN. UniquequotientppavResEhasreducibleproducttheta,soONLYfixedq223F223polarized(2,2,2)Jacobiantargetrouteisobstructed. PrimaryMumford1971/MilneAV/JVactuallyread/pinned. Thisdoesnotexcludeotherdegrees/fields/polarizations/longerchains. FiveexactpartialLean392a95/039ca3/9f99f1/e7e736/ea637d passbothoriginalgates8decls(5named3generated)/0trusted;first redundantgeneralizingfailure6956b2 retained/all5statementhashesunchanged. Wholeproof13efa5/9aaaea/0787d4. THREE59824bytePDFpagesALLinspected/9ba899,proposalexplicit. [pcc:unverified]

Newf1d44f GLUING_CHAIN_PROPOSAL_01 freezesproposedJ->ResE->Jprime usingDIFFERENTgluing,expectedA2kernel9/3product6gluingcountuntested. All3actualsource2roots/BOTHh-signs;Hdiaghi/offdiag-Ai,QadjH,D16detH,quotient/smoothness/twist/projectiveinvariantidentitiesREQUIREindependentchecks. PrimaryHLPmath9809210 found/downloaded,Prop15formulacomparisonNEXT. No newcurve/nondualmap/advantageclaimed. Newdfa5bfstrictkernelCIplan precedesci_kernels/separateworkflow;554portableinputs348producer/15positivephases/all8wholeJSON+everybinarybyte/bothoriginal8declgates/5bindings. Owncleanfull/fouradmission/CIpending. [pcc:unverified]

Parent85b799ec/158paths/2c19d2 normalpublished0. Exact85bindependentfullaf9044/all523guards/11phases/fourcontrols andallSIXworkflowsf9535f/all50native25canonicaldigests match. ExtraPCC43460007347successobservedinrunsAPI,notadditionalwholelogclaimed. TENpriorclosedtreesgenuinelyf824e8/39084d13S3+7smallGit/rootb023 normalpush0/55b40b;newtwo-primaryfull/CI/bitangentnative/full/CI/census/replay/fullCIrawsneedNEXTwholehandoff. No nativeprocessinflight. [pcc:unverified]

Persistentnext: normalpublishsource+CI554;cleanphysical554+self555sourceclosure/pinned3dproducer(originalSmith20532f46sameascurrent),fouractualadmissioncontrols,originalfull. ThenreadHLP4.1/Prop15andvalidateall6proposedgluingmodels/actualA2kernelcoordinateswithoriginalRust+faithfulLean;constructsurvivingmapsandboth[4]chain/publicoddpoints. Preserveallnulls/failures/twists/singularmodels. NewwholedatahandoffrequiresfreshcompleteguardincludingCensus/Replay/newmath. Originalbenchmarkcheckpoint/livebudget/capacity/completecost/strongestrefs,fullgeometricformal/mainfrozenledger/signing/review/conflict/globalfixture/vault/KB gapsremain. Nextglobalroutine17:45UTCunlessmaterialsignal. Continueaftereachrung. [pcc:unverified]
