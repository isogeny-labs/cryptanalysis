# Literature and implementation review before approach selection

Review completed before new arithmetic source or scientific calls. The shared
KB and Conductor tools are absent after enabled-tool discovery; the locked
autoresearcher wrapper was not opened or executed. Connected GitHub/web
fallback is recorded below and provides no novelty clearance. [pcc:unverified]

- Galbraith, *Mathematics of Public Key Cryptography*, corrected chapter10:
  https://www.math.auckland.ac.nz/~sgal018/crypto-book/ch10.pdf . Read
  Definition10.1.16 (inert model), Lemma10.3.5 and its multiplicity proof,
  Theorem10.3.14 and complete composition proof, reduction10.11/Lemma10.3.17,
  degree bounds10.3.20, and the split-model uniqueness proof10.4.19.
  Composition concerns affine divisors; the final divisor-class operation
  must account for infinity. Its odd-degree theorem10.3.21 is not imported
  for this sextic. Our inert-model specialization is derived separately.
- Galbraith--Harrison--Mireles Morales, *Efficient Hyperelliptic Arithmetic
  Using Balanced Representation for Divisors*, ANTS-VIII/LNCS5011 (2008),
  342-356: https://cspages.ucalgary.ca/~rscheidl/pims/handouts/GalbraithHarrisonMorales.pdf .
  Read section2 definitions/proposition1 and proofs, section3 algorithms1/2
  with divisor counterweights, section4 algorithm4 and the explicit even-genus
  nonrational-infinity observation on page352. Equal counterweights eliminate
  the infinity-balancing step. This is the established method used here;
  its split-leading-term branches and generic performance comparisons are
  not new claims about this fixed curve. [pcc:unverified]
- Cantor (1987), Math.Comp.48,95-101, DOI10.1090/S0025-5718-1987-0866101-0:
  the primary AMS PDF returned403. Its text was not read or cited as if read;
  the complete composition/reduction derivations above were accessible.
- Repository review: original crypto5114 bbc54625 actual model, two covers,
  ordered gluing proof d80057 and global retraction8b16d2; all original native
  A-D certificates. Read crypto `src/cryptanalysis/genus2_fp.rs` introduction
  and constructor scope (exact quintic), `hyperelliptic_word.rs` introduction
  (degree2g+1), and cryptanalysis `suite/src/binary_ecc/hyperelliptic.rs`
  checked odd-degree/characteristic-two scope. Reuse the small qualified F7
  polynomial primitives; the complete inert sextic/actual-cover audit needs
  a separate scoped implementation. The broad connected search also located
  these existing Cantor modules; unrelated matches were excluded.
- Two initially guessed cryptanalysis paths for the prime modules returned
  404; they are in crypto, while the available cryptanalysis native module
  explicitly covers characteristic two. The math sources and existing-code
  scope, rather than the guessed paths, determine this implementation.
- Bootstrap metadata negatives: an unanchored heading assertion saw an
  embedded template; a dependent stage was mistakenly attempted after that
  failure and rejected a sparse-index tree mismatch. Exact failed candidate
  is retained. Anchored heading and valid cone patterns correct metadata;
  ACTIVE-only25e3635e and draft1964 preceded this review and any research code.

No parameter search, runtime measurement, new solver or novelty claim is
selected. This is complete fixed-object divisor/group correctness under the
named existing mathematics. Independent actual-root pushforwards are a
separate arithmetic route within the same unsigned producer, not a signed
independent verification verdict. [pcc:unverified]
