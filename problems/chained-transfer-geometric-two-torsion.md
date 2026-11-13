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


## 2026-11-13 — actual alternative route and remaining validation

Nativef33c42/7c9bf4 and written5f7e4c now supplyALLsixclassicalHLPproductgluings/fourcompletePhiPrime/NPrime/both2+both4/allfivepublictargets/threeendpointsdifferentfromoldoverF223. Literaloriginalcontrol/twononsquaretwists/allC4cofactornegative retained. ElevennewfaithfulpartialLeanbindings/bothoriginalgates;fullgeometry/signedexecution/costremainopen. Kernelindependentfullb9cd55/CI48edee settled;newgluingci596/21phases/owncleanfull597+8workflowauditpending. This advances the broader route without removing the fixed-J polarized-degree obstruction or constructing an actual geometric divisor basis for its fullJ[2]. See GLUING_CHAIN_DERIVATION_01.md/GLUING_PROOF_MAP_01.md and reports/alternative-gluing-01. Next publishsource,cleanfull+CI,wholedatahandoff,thenchainkernelstructure and collapse-aware furtherwalks;originalbenchmarkadmissionstillrequired. [pcc:unverified]


## 2026-11-13T19:32:04.837885+00:00 — actual chain kernels, same-product collapse and genuine publication

Published gluing source7cf45856 is settled: independent full06b112 passes all597 guards/21 ordered phase pairs/two unfiltered tests/ALL18 whole JSON/11 canonical bindings and four actual admission controls. Own eight-workflow CIaefb67 succeeds with all76 native records and41 canonical proof digests. Do not repeat settled runs. [pcc:unverified]

Genuine e5f4c5/consumer74b399 publishes seventeen complete closed captures:34 original objects,26 S3 and8 small complete indices in Git. Actual pull_request_target run43488304162/job132102493726 replays26 remote objects BEFORE bot3bc395c25, direct parentf4565b1f/exact28 paths. Exact FF/artifact/wiring0; all3096 selected inputs and both repositories' owned dirty bytes preserved. All original physical objects remain intact. Root final metadata4cce14d0 is normally published0. Guard05 is historical and released; every future FF needs a new complete current guard06. [pcc:unverified]

Prospective a94132 precedes chain-kernels code. Native29830a passes one unfiltered test/all2432 inputs unchanged: all135 independently matched original Lagrangians/4096 pairings; Gold intersection histogram64/56/14/1; entire9x9 rational intersection table with actual A[2] triples; all128 actual repeated routes. Written2e21d5 derives geometric ker(F)=C4^(3-d) x C2^(2d), d=dim(Gold intersect G). Eligible dimensions0/1/3/0 give two free maximal-isotropic(4,4,4) kernels, one nonfree kernel, and the literal [2] control. Actual rational kernels all contain2 points and do not distinguish these geometric types. No J[4] divisor basis is constructed. [pcc:unverified]

The global same-product identity reduces an L-edge path to [2^(L-1)] times its direct endpoint transfer. This is a negative result for obtaining new normalized homomorphisms by extending such paths. It supplies no implementation cost lower bound and preserves the three distinct one-step endpoints. Three faithful partial exact Lean bindings cbaaa0/580339/0cc751 pass both unchanged original gates/zero trusted,44 local bindings total. Whole producer/consumer proof captures a37330/a81a8a; final two60785-byte PDF pages ALL inspected/dda668. Geometry, torsion exactness, group classification, polarization and Picard interpretation remain written bridges. [pcc:unverified]

Prospective1418f3 precedes additive ci_chain/ninth workflow. New frozen inventory616 portable/348 producer plus manifest self617; ten positive native/tee pairs, one unfiltered native test/ALL4 whole JSON exact/no exclusions/both original3-declaration gates/three bindings. Own published-source clean physical full, four actual admission controls and nine-workflow CI audit80 native44 canonical digests are NEXT, not completed. Previous eight workflows and all frozen source bytes remain unchanged. [pcc:unverified]

Persistent next actions: normal source commit/push; materialize exact clean new source and original3d producer as physical siblings, four controls then bounded2100s full/fresh outside cache; collect nine workflows. During isolated replay, freeze a new protocol for the actual degree13 source isogeny and normalized dual using original division polynomials/Kohel/SEA, exact whole polynomial identities and all source/public/cofactor controls. Its proposed Res(Eprime) route must demonstrate actual new products/maps before expected [52] compositions can be results. No new isogeny or advantage is yet claimed. [pcc:unverified]

Main3877 remains open/conflicting and ready1519/1523 open/mergeable at19:30 read; no force/rebase/rechain/ledger-lineage choice or merge waiver. Original benchmark S3 checkpoint/live budget/capacity and complete costs/strongest references are still absent; only bounded local correctness and CI development proceed. Authentic global-root fixture, full formal geometry, vault8edec422 and KB/ecdb access remain unresolved. Continue after this rung; no native job is currently running. [pcc:unverified]


## 2026-11-13T19:59:57.594812+00:00 — actual degree13 source and different product

Kernel sourcea7ea5998/governancecfb8fa/normalpublication0aa36b is settled. Independentfullf4c0a7/all617 guards/ten phasepairs/ALL4 whole JSON/both original3-declaration gates/3 canonical bindings/four actual controls passes. Own NINE workflows6add5b allSUCCESS/all80 native44 canonical proof digests match; duplicate PCC43493242015 alsoSUCCESS observed in full inventory,latest43493579772 captured once. Whole native/log/API/source captures remain local with exact catalogues, queued for genuine whole publication. No unchanged science redispatch. [pcc:unverified]

Prospectivee9234b precedes actual odd-source native02/de87bd. Over K=F223[z]/(z³-3), actual target Eprime has a=(196,168,69),b=(8,82,207), full ID N4-E13-short-936b863521fdce08d2724c468f27979cb39d9443d082b4be14209bb08f408414. Original division-polynomial/Frobenius/Kohel/SEA engines give degree13 gamma and normalized dual delta/eigenvalues2,4. Both whole coefficient curve identities and BOTH full x/y[13] composition cross-polynomials vanish;degree169/168,coprime. All36source/36target/1024hom pairs each/full4E2bijection/nonzeroexactell2773073/allfive public targets pass,all2452 selected inputs unchanged. First compile101/1ea2d5 retained before only original-square API repair. [pcc:unverified]

Actual source and target j-conjugate sets are disjoint. Writtenb9a91f gives proper extension/O-preserving homomorphism/degree/dual and finite rational-group injection/order-equality arguments, plus polarized-product distinction. This supplies a DIFFERENT product Aprime, not a new Jacobian yet. Odd inverse639940 delta and whole-group inverse3413013 delta have distinct scopes. Six faithful partial exact Lean bindings c6dca4/796f92/7781ea/ee0e7e/82763b/caa2b3 pass both original4.35/4.34.1 gates/zero trusted,50 local bindings total. Original PATH not-covered78ddb7 preserved; SAME first claim laterpasses after caller PATH only. Whole proofsb32320/67342c; final TWO55957-byte PDF pages ALL inspected/1ea6c9. Full geometric bridges remain written/open. [pcc:unverified]

Prospective435ad0 precedes additive ci_odd/separate TENTH workflow, all previous nine unchanged. New639 portable inputs348producer+self640;thirteen positive native/tee phases,one unfiltered test/ALL4 whole JSON exact/no exclusions/both original6-declaration gates/six exact bindings. Own published-source clean physical full/four actual admission controls/ten-workflow audit84 native50 canonical digests are NEXT, not completed. [pcc:unverified]

Frozen56fbbb ODD_PRODUCT_GLUING_PROTOCOL_01.md now precedes new Aprime model/map code: fresh explicit source type from actual gamma target, old-panel parity ALL6, then all6 new HLP sign outcomes/all135 product kernels/actual coordinate/Frobenius/descent/quotient checks. Keep every singular/Tzero/nonsquare/duplicate. For each eligible source build fresh complete Phi/Norm/both2/origins/exceptional controls, then BOTH[52] on all224old and allnew rational C-point classes/nonzeroell/allpublic5/cofactor tables/159985 inverse. Expected degree140608 and endpoint distinction stay conditional until actual new maps. [pcc:unverified]

Next: normal source checkpoint/push, clean640-input physical original3d replay/four controls/full2100s/fresh cache, collect ten workflows. While isolated replay runs, implement fresh typed generic HLP model builder and parity/source-coordinate checks under56fbbb; then actual new complete maps and chain52, written/formal/report/ownCI. Whole kernel full/CI/oddsource failed+success captures need next unchanged genuine publisher with complete current guard06 before any root botFF. Prior seventeen captures genuinee5f4c5/74b399 and root4cce14d0 normalpublication remain settled;all physical originals intact. [pcc:unverified]

No benchmark admission or computational advantage: original S3 checkpoint/live budget/capacity/fullcost/strongestrefs remain unresolved. Root authentic fixture/global library gate, main append-only ledger/signing/reviews/conflict, full formal geometry, locked vault8edec422 and KB/ecdb access remain open. Workspace1.5GiB free at19:50; preserve evidence and keep root regression binary/warm correctness cache, remove only obsolete derived caches if needed. No native process currently running; all proof processes terminal. Continue after this rung. [pcc:unverified]
