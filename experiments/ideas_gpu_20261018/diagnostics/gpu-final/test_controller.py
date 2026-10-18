"""Offline GPU continuation controls: no real network, keys, or provider calls."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parents[1]/"run_gpu_final.py"
with patch("urllib.request.urlopen",side_effect=AssertionError("network forbidden")),patch("subprocess.Popen",side_effect=AssertionError("process forbidden")):
    spec=importlib.util.spec_from_file_location("gpu_final_transport",SCRIPT)
    c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
COMMIT="1"*40
NONCE="SYNTHETIC-NONCE-"*4

class FakeClient:
    def __init__(self,failures=(),change=None,status=201):
        self.failures=list(failures); self.change=change or {}; self.status=status
        self.events=[]; self.created=[]; self.deleted=[]
    def safe_detail(self,error):
        return "synthetic refusal"
    def call(self,method,path,body=None,timeout=30):
        if path.startswith("/catalog/gpus"):
            return 200,{"gpus":[dict(id=f,manufacturer="NVIDIA",community=True,
                maxCount=dict(community=1),price=dict(community=.69),availability="HIGH") for f in c.FLAVORS]}
        if method=="GET" and path.startswith("/pods?"):
            return 200,{"pods":[],"pagination":{"hasNextPage":False,"nextCursor":None}}
        if method=="POST":
            self.events.append("post"); self.created.append(deepcopy(body))
            if self.failures:
                raise c.ProviderError(self.failures.pop(0),"synthetic capacity refusal")
            pod=dict(id="ownedPod123",name=body["name"],cloud="COMMUNITY",image=c.IMAGE,
                gpu=dict(id=body["gpu"]["id"],count=1,vcpuCount=16,memory=32),cost=.69,
                cudaVersion="13.0",status="PROVISIONING",env=body["env"])
            pod.update(self.change)
            return self.status,pod
        if method=="DELETE":
            self.deleted.append(path); return 204,None
        if method=="GET" and path=="/pods/ownedPod123":
            raise c.ProviderError(404,"absent")
        raise AssertionError((method,path))

class Controls(unittest.TestCase):
    def run_mock(self,client,study,**changes):
        output=study/"resource-runs/gpu-final-01"
        def armed(*args):
            client.events.append("watchdog_armed")
        with patch.object(c,"STUDY",study),patch.dict("os.environ",{"RUNPOD_API_KEY":"SYNTHETIC-NOT-A-CREDENTIAL"},clear=True),patch.object(c,"public_source",return_value="https://public.invalid/pinned.tar.gz"),patch.object(c,"prove_public_source",return_value=dict(sha256=c.PAYLOAD_SHA256,authorization_header_supplied=False)),patch.object(c,"start_watchdog",side_effect=armed),patch.object(c,"fetch_job",return_value=dict(results_fetched=True,workflow_returncode=0)),redirect_stdout(io.StringIO()):
            return c.execute(COMMIT,output,client_factory=lambda *a,**k:client)

    def test_official_schema_exact_gpu_count_cuda_and_no_cpu(self):
        schema=json.loads((HERE.parent/"cpu-v2-api/official-create-schema.json").read_text())
        validator=Draft202012Validator(schema)
        for flavor in c.FLAVORS:
            body=c.create_body(flavor,"ideas-20261018-gpu-final-0123456789abcdef","https://public.invalid/pinned",NONCE)
            self.assertEqual(list(validator.iter_errors(body)),[])
            self.assertNotIn("cpu",body); self.assertFalse(body["startJupyter"]); self.assertFalse(body["startSsh"])
            self.assertEqual(body["gpu"],dict(id=flavor,count=1,minCudaVersion="13.0",minRamPerGpu=32,minVcpuCountPerGpu=16))
            self.assertIn("remote_http_gpu_v3.py --out /root/cryptanalysis/experiments/ideas_gpu_20261018/remote/run-gpu-v3",body["cmd"][0])
            invalid=deepcopy(body); invalid["gpu"]["minRAMPerGPU"]=32
            self.assertTrue(list(validator.iter_errors(invalid)))

    def test_plan_import_need_no_key_network_or_provider(self):
        with patch.dict("os.environ",{},clear=True),patch.object(c.urllib.request,"urlopen",side_effect=AssertionError("network forbidden")),redirect_stdout(io.StringIO()) as out,patch.object(sys,"argv",[str(SCRIPT),"plan","--source-commit",COMMIT]):
            c.main()
        planned=json.loads(out.getvalue())
        self.assertIs(planned["provider_actions"],False)
        self.assertEqual(planned["maximum_price_per_hour"],1.5)
        self.assertEqual(planned["maximum_actual_pods"],1)
        self.assertEqual(planned["maximum_seconds"],3600)
        self.assertEqual(planned["cleanup_begins_seconds"],3300)

    def test_public_proof_is_unauthenticated_and_exact_hash_checked(self):
        response=MagicMock(); response.__enter__.return_value=response
        response.read.return_value=(c.STUDY/"remote-payload-v5.tar.gz").read_bytes()
        with patch.object(c.urllib.request,"urlopen",return_value=response) as opened:
            result=c.prove_public_source(c.public_source(COMMIT))
        self.assertFalse(result["authorization_header_supplied"])
        self.assertNotIn("Authorization",dict(opened.call_args.args[0].header_items()))
        response.read.return_value=b"corrupted"
        with patch.object(c.urllib.request,"urlopen",return_value=response),self.assertRaises(ValueError):
            c.prove_public_source(c.public_source(COMMIT))

    def test_explicit_refusal_fallback_then_one_actual_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            study=Path(temporary); client=FakeClient(failures=[400,403])
            self.run_mock(client,study)
            self.assertEqual([p["gpu"]["id"] for p in client.created],list(c.FLAVORS))
            self.assertEqual(client.deleted,["/pods/ownedPod123"])
            self.assertEqual(client.events[:2],["watchdog_armed","post"])
            output=study/"resource-runs/gpu-final-01"
            all_text="".join(p.read_text() for p in output.rglob("*") if p.is_file())
            self.assertNotIn("SYNTHETIC-NOT-A-CREDENTIAL",all_text)
            self.assertNotIn(client.created[-1]["env"]["IDEAS_HTTP_BEARER"],all_text)
            with self.assertRaises(FileExistsError):
                self.run_mock(client,study)

    def test_first_creation_stops_all_other_gpu_requests(self):
        with tempfile.TemporaryDirectory() as temporary:
            client=FakeClient(); self.run_mock(client,Path(temporary))
            self.assertEqual(len(client.created),1)

    def test_ambiguous_500_has_no_retry_or_false_no_pod_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            client=FakeClient(failures=[500])
            with self.assertRaises(RuntimeError):
                self.run_mock(client,Path(temporary))
            self.assertEqual(len(client.created),1)
            output=Path(temporary)/"resource-runs/gpu-final-01"
            self.assertTrue((output/"ownership-intent.json").exists())
            outcome=c.read_json(output/"resource-outcome.json")
            self.assertFalse(outcome["absence_verified"])

    def test_allocated_guard_failures_cleanup_one_exact_id_without_retry(self):
        cases=[dict(cost=1.51),dict(cost=True),dict(cost=float("nan")),dict(cudaVersion="12.9"),
            dict(cudaVersion=None),dict(gpu=dict(id=c.FLAVORS[0],count=2,vcpuCount=16,memory=32)),
            dict(gpu=dict(id=c.FLAVORS[0],count=1,vcpuCount=15,memory=32)),
            dict(gpu=dict(id=c.FLAVORS[0],count=1,vcpuCount=16,memory=31))]
        for change in cases:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as temporary:
                client=FakeClient(change=change)
                with self.assertRaises(ValueError):
                    self.run_mock(client,Path(temporary))
                self.assertEqual(len(client.created),1)
                self.assertEqual(client.deleted,["/pods/ownedPod123"])

    def test_watchdog_failure_blocks_every_post(self):
        with tempfile.TemporaryDirectory() as temporary:
            study=Path(temporary); client=FakeClient()
            with patch.object(c,"STUDY",study),patch.dict("os.environ",{"RUNPOD_API_KEY":"SYNTHETIC-NOT-A-CREDENTIAL"}),patch.object(c,"public_source",return_value="https://public.invalid/pinned"),patch.object(c,"prove_public_source",return_value={}),patch.object(c,"start_watchdog",side_effect=RuntimeError("synthetic watchdog failure")),self.assertRaises(RuntimeError):
                c.execute(COMMIT,study/"resource-runs/gpu-final-01",client_factory=lambda *a,**k:client)
            self.assertEqual(client.created,[])

    def test_wrong_local_output_and_old_run_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as temporary,patch.object(c,"STUDY",Path(temporary)):
            for path in (Path(temporary)/"remote/run-gpu-v3",Path(temporary)/"resource-runs/gpu-final-02"):
                with self.assertRaises(ValueError):
                    c.execute(COMMIT,path)
                self.assertFalse(path.exists())

    def test_catalog_order_price_and_false_number_guards(self):
        client=FakeClient(); status,body=client.call("GET","/catalog/gpus")
        selected=c.selected_catalog(client)
        self.assertEqual([p["id"] for p in selected],list(c.FLAVORS))
        for bad in (True,float("nan"),-1,1.51):
            changed=deepcopy(body)
            for row in changed["gpus"]:
                row["price"]["community"]=bad
            with patch.object(client,"call",return_value=(status,changed)),self.assertRaises(ValueError):
                c.selected_catalog(client)

    def test_redirect_never_forwards_provider_or_http_bearer(self):
        self.assertIsNone(c.NoRedirect().redirect_request(None,None,302,"redirect",{},"https://unrelated.invalid"))

    def make_archive(self,members):
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode="w:gz") as archive:
            for name,data in members:
                item=tarfile.TarInfo(name); item.size=len(data)
                archive.addfile(item,io.BytesIO(data))
        return stream.getvalue()

    def fetch_fixture(self,temporary,payload):
        status=dict(done=True,archive_ready=True,archive_sha256=hashlib.sha256(payload).hexdigest(),archive_bytes=len(payload),returncode=3)
        def request(base,path,bearer,timeout=30):
            return io.BytesIO(json.dumps(status).encode() if path=="/status" else payload)
        with patch.object(c,"evidence_request",side_effect=request):
            return c.fetch_job(dict(id="ownedPod123"),NONCE,Path(temporary),c.time.monotonic()+10)

    def test_fresh_archive_and_complete_independent_member_hashes(self):
        data=b"fixture failure retained\n"; digest=hashlib.sha256(data).hexdigest()
        payload=self.make_archive([("remote/run-gpu-v3/started.utc",data),("remote/run-gpu-v3/http-evidence-files.sha256",(digest+"  started.utc\n").encode())])
        with tempfile.TemporaryDirectory() as temporary:
            result=self.fetch_fixture(temporary,payload)
            self.assertTrue(result["results_fetched"]); self.assertEqual(result["workflow_returncode"],3)
            self.assertEqual((Path(temporary)/"evidence/remote/run-gpu-v3/started.utc").read_bytes(),data)
            self.assertTrue(c.read_json(Path(temporary)/"evidence-verification.json")["exact_member_coverage"])
            with self.assertRaises(FileExistsError):
                self.fetch_fixture(temporary,payload)

    def test_traversal_other_run_duplicate_and_unmanifested_member_refused(self):
        for members in ([('remote/run-gpu-v3/../escape',b'x')],[('remote/run-1/file',b'x')],
            [('remote/run-gpu-v3/a',b'x'),('remote/run-gpu-v3/a',b'y')],
            [('remote/run-gpu-v3/unlisted',b'x'),('remote/run-gpu-v3/http-evidence-files.sha256',b'')]):
            with self.subTest(members=members),tempfile.TemporaryDirectory() as temporary,self.assertRaises(ValueError):
                self.fetch_fixture(temporary,self.make_archive(members))

    def test_cleanup_retries_even_if_failure_receipt_cannot_be_written(self):
        client=MagicMock(); client.call.side_effect=[c.ProviderError(500,"transient"),(204,None),c.ProviderError(404,"absent")]
        with tempfile.TemporaryDirectory() as temporary,patch.object(c.time,"sleep"),patch.object(c,"write_once",side_effect=OSError("synthetic disk failure")):
            self.assertTrue(c.cleanup_until_absent(client,dict(id="ownedPod123",expires_unix=10**12),Path(temporary))["absence_verified"])

    def test_atomic_receipts_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"record.json"; c.write_once(path,{"complete":True})
            with self.assertRaises(FileExistsError):
                c.write_once(path,{"overwrite":True})
            self.assertEqual(c.read_json(path),{"complete":True})

    def test_prepost_watchdog_reconciles_late_nonce_bound_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"ownership-intent.json"
            path.write_text(json.dumps(dict(schema=c.ARTIFACT_VERSION+"/intent",api_base=c.API,
                name="ideas-20261018-gpu-final-0123456789abcdef",started_unix=0,expires_unix=3600,maximum_seconds=3600,
                http_bearer_sha256=hashlib.sha256(NONCE.encode()).hexdigest())))
            (Path(temporary)/"ownership.json").write_text('{"partial":')
            pod=dict(id="lateOwned123",env=dict(IDEAS_HTTP_BEARER=NONCE))
            with patch.object(c.time,"time",return_value=3300),patch.object(c.time,"sleep"),patch.object(c,"named_pods",side_effect=[[],[pod]]),patch.object(c,"cleanup_until_absent",return_value=dict(id="lateOwned123",absence_verified=True)) as cleanup:
                c.intent_watchdog(path,MagicMock(),NONCE)
            self.assertEqual(cleanup.call_args.args[1]["id"],"lateOwned123")

if __name__=="__main__":
    unittest.main(verbosity=2)
