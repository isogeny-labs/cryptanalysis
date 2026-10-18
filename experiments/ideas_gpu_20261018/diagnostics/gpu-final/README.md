# Final bounded GPU continuation: source preparation

Status: prospective infrastructure only. This directory contains offline software controls and a local plan; it contains no new provider allocation or scientific measurement.

The unchanged public `remote-payload-v5.tar.gz` supplies the fixed native workload and corrected v2 ingestion checker. The controller derives its pre-POST intent/watchdog, exact-ID cleanup, and public-source proof safeguards from the frozen `run_cpu_v2_api.py`; that file was not edited. GPU request fields are validated against the previously captured official OpenAPI closure in `../cpu-v2-api/official-create-schema.json` and its existing provenance.

`software-controls-02.stderr` records all 16 passing offline controls. They cover source proof without Authorization, exact payload hashes, credential-free import/plan, documented GPU request schema, price/CUDA/RAM/vCPU gates, explicit refusal fallback, no second create after an actual or ambiguous creation, watchdog-before-POST, fresh extraction/no overwrite, archive traversal/duplicate/member-hash rejection, and cleanup through transient API or receipt-disk failures. The first control attempt is retained as `software-controls-01.*`: two errors were caused by a 39-character synthetic source-commit fixture; the fixture was corrected to 40 hex characters before the passing run. No scientific source or workload changed.

A runnable preparation command is:

```sh
python3 experiments/ideas_gpu_20261018/run_gpu_final.py plan --source-commit PUBLISHED_40_HEX_COMMIT
```

After root reviews and publishes the prospective packet, root can use its existing local environment credential and run:

```sh
python3 experiments/ideas_gpu_20261018/run_gpu_final.py execute --source-commit PUBLISHED_40_HEX_COMMIT --out /workspace/cryptanalysis/experiments/ideas_gpu_20261018/resource-runs/gpu-final-01
```

The destination must not exist. The internal archive may retain `remote/run-gpu-v3`, but extraction occurs only under the fresh `resource-runs/gpu-final-01/evidence` directory. The controller refuses all other output roots. This prevents overwriting the preserved failed-host run.

This is one additional actual pod at most, with a reported rate guard of USD 1.50/hour, a 3600-second target, and independent cleanup beginning at 3300 seconds. Neither software nor provider availability provides an invoice ceiling or a provider-enforced TTL. API outages can delay deletion; the watchdog preserves the violation and continues exact-ID deletion until absence is verified. The native GPU gates and independent frontier outcome must be reported separately; a successful bounded GPU diagnostic is not a challenge solution.

The global graphs describe mathematical mechanisms and recorded measurements; this source-only transport preparation changes neither. Existing GPU result reports and prior raw evidence remain unchanged.
