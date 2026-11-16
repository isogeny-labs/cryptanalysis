# Whole LP runtime packaging context

This component assembles the complete image input bytes and a source-only Docker recipe. It performs file copying, hashing and metadata checks. It invokes no Docker, AWS, compiler or scientific binary. Final metadata context4ba9e2 has308 whole files/575,053,199 logical bytes and all byte phases0. Original immutable archive/build files are hardlinked; their bytes and permissions are unchanged. The complete first/second/final contexts remain separately held. [pcc:unverified]

The context keeps the whole original340,729,140-byte baseline CI ZIP and the whole53,419,171-byte pure compiler CI ZIP, the complete39,331,840-byte guarded source snapshot, all selected baseline/prepared-engine members, actual new compiled entrypoints/compiler/source receipts, six compressed fixtures and the complete passive capture. The two archives remain whole even though selected files are also materialized. The final inventory and separately repeated destination/archive/native/fixture pins are retained. [pcc:unverified]

Run the file-only assembler with existing complete inputs and a fresh output directory on the same filesystem as the immutable data holds:

```sh
bash assemble-context-01.sh CONSUMER_REPO GUARDED_SNAPSHOT BASELINE_CAPSULE PURE_BUILD PURE_CI_ZIP ORIGINAL_FIXTURE_DIR FRESH_OUTPUT
```

The helper records every phase's argv/stdout/stderr/exit, the actual recipe checkout head and its complete status. It preserves its actual command bytes separately. An unpublished helper is not relabelled as part of its checkout HEAD. Compiler source2c44ee2e, original baseline Consumerb7b919/upstream3d49af7, guarded Root44a3db and the actual recipe revision are recorded separately. [pcc:unverified]

The official Debian linux/amd64 base manifest/config was actually fetched as metadata3a72e2: leaf digestc67e92c8099ba22853ab4cfda7cfb494d253d6012ca82dee98ba8976772af018. No layers were downloaded. The recipe installs the runtime utilities and pinned AWS CLI1.46.2, recording the actual package lists during a future build. Actual library compatibility, package/install outcomes and OCI digest are unqualified until that build and runtime checks occur. [pcc:unverified]

The first recipe's source review found root-owned mode600 data would be unreadable by UID1000. The corrected explicit COPY ownership preserves original host files and gives the image's runtime user access. It also requires the actual source-status receipt to be empty and the supplied recipe revision to match the exact checkout HEAD. This intentionally prevents the present dirty/unpublished recipe context from becoming a qualified image build. First contextb75dd8 remains complete; it is not an observed failed image execution. [pcc:unverified]

Actual account budgets e42949 stop new paid builds/jobs. No image was built, published or executed. A future paid build additionally needs the published clean recipe and unchanged check-experiment-git, original live budget/lane reservation/pool admission, complete build/cost custody and actual OCI/native/Job/Pod identities. This packaging does not supply an actual runtime Git checkout, original checkpoint or full historical LP execution. The next component must materialize the exact native-source2c clean checkout/committed RESUME and ignored raw bytes, qualify the source snapshot and unchanged1605/50/12 guards, route the unchanged checkpoint through the existing assigned identity, and hand off under the original frozen absolute deadline. [pcc:unverified]

Use the maintained generic isolab.eks.command-request/v1 contract for a later reviewed launcher. These tools do not satisfy the ecbench-specific three-field build contract. Full60/240/62/original360/witness/control/feedback/post requirements and scientific NEW28 remain open at their original scopes. [pcc:unverified]
