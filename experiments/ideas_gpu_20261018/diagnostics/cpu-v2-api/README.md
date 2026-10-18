# CPU API-v2 controller preparation

Source preparation only. No credentials, network/provider calls or pod creation occurred in this task. Root owns publication, public-source proof and any subsequent launch.

The new controller is `../../run_cpu_v2_api.py`; the prospective amendment is `../../CPU-V2-API-PROSPECTIVE-AMENDMENT.json`. Both CPU request bodies validate against the 13-schema closure copied from the root-provided official OpenAPI snapshot. Its original SHA256 is `77e8caf5a60b390026abcdded5893d45d7d79bae3ddf70030604f58845d80bc5`; see `schema-provenance.json`. The implementation uses v2 nested CPU fields and v2 response price/resources, rather than the existing controller's v1 body.

Twelve final offline tests pass in 0.144 seconds. They cover schema validation, pagination, 400/403 fallback versus uncertain 500 stop, resource rejection cleanup, secret-free records, redirect refusal, pre-POST watchdog arming, delayed resource visibility, atomic no-overwrite receipts, corrupt ownership, diagnostic disk failures and retrying exact-ID cleanup. Provider credentials in controls are explicitly synthetic; actual calls/process starts are mocked. `software-controls-02.*` binds the final source and nine exact dependencies. The initial iterative control log remains retained. These are infrastructure controls, not native-science or provider execution results. Additional internal source review found no blocking defect in the final code.

The payload remains v5, SHA256 `e269ad82ff1ff7724d88ccd34adf3752f642f9895f2dd015889315245fbfcfd4`, with unchanged fixed command, setup/scientific timeouts and CPU labels. Requests try cpu3m then cpu5m only after explicit refusal,32vCPU/256GB and positive price at most2.10USD/hour. A durable intent and detached ready-acknowledged watchdog precede the first POST. It handles ambiguous creation using fresh-name plus nonce attribution. Both ordinary and watchdog cleanup delete only exact attributable IDs and verify GET404. No unrelated pods are changed. Provider/evidence requests refuse redirects carrying Authorization.

The target maximum is2700seconds; independent cleanup starts at2400seconds. API-v2 supplies no provider TTL, so a provider/network outage can defeat a hard billing deadline. The controller records overruns and keeps cleanup alive instead of claiming guaranteed termination. This limitation is part of the prospective amendment.

From repository root, inspect without credentials or network:

```sh
python3 experiments/ideas_gpu_20261018/run_cpu_v2_api.py plan --source-commit 67272e08a7f6bd9b4cf62914013caef96daad769
```

After root publishes/reviews the source and explicitly launches, with its existing ephemeral key environment and a fresh output directory:

```sh
python3 experiments/ideas_gpu_20261018/run_cpu_v2_api.py execute --source-commit 67272e08a7f6bd9b4cf62914013caef96daad769 --out experiments/ideas_gpu_20261018/resource-runs/cpu-api-v2-01
```

The execute mode proves unauthenticated public payload bytes before reading a key. It starts its independent intent watchdog automatically. Existing root exact-ID watchdog tooling can consume `ownership.json` fields id/name/started_unix/maximum_seconds/api_base/delete_url/expires_unix; the direct equivalent is `watchdog --ownership <ownership.json>`. The `cleanup --ownership <ownership.json>` command performs exact-ID deletion and absence verification. Neither command is run during preparation. Evidence stays under the fresh output directory, preserving all earlier refusals and reports.
