"""Offline transport/software controls. No real credentials, network or pods."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,MagicMock

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parents[1]/"run_cpu_v2_api.py"
with patch("urllib.request.urlopen",side_effect=AssertionError("network forbidden")),patch("subprocess.Popen",side_effect=AssertionError("process forbidden")):
    spec=importlib.util.spec_from_file_location("cpu_v2_transport",SCRIPT)
    c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
COMMIT="67272e08a7f6bd9b4cf62914013caef96daad769"


class FakeClient:
    def __init__(self,failures=(),change=None,status=201,events=None):
        self.failures=list(failures); self.change=change or {}; self.status=status
        self.events=events if events is not None else []; self.created=[]; self.deleted=[]
    def safe_detail(self,error):
        return "synthetic refusal"
    def call(self,method,path,body=None,timeout=30):
        if path.startswith("/catalog/cpus"):
            return 200,{"cpus":[dict(id=f,vcpu=dict(min=2,max=32),ramGbPerVcpu=8,
                price=dict(securePerVcpu=.055 if f=="cpu3m" else .065),availability="HIGH") for f in c.FLAVORS]}
        if method=="GET" and path.startswith("/pods?"):
            return 200,{"pods":[],"pagination":{"hasNextPage":False,"nextCursor":None}}
        if method=="POST":
            self.events.append("post"); self.created.append(deepcopy(body))
            if self.failures:
                raise c.ProviderError(self.failures.pop(0),"synthetic refusal")
            pod=dict(id="ownedPod123",name=body["name"],cloud="SECURE",image=c.IMAGE,
                cpu=dict(id=body["cpu"]["id"],vcpuCount=32,memory=256),cost=1.76,status="PROVISIONING",env=body["env"])
            pod.update(self.change)
            return self.status,pod
        if method=="DELETE":
            self.deleted.append(path); return 204,None
        if method=="GET" and path=="/pods/ownedPod123":
            raise c.ProviderError(404,"absent")
        raise AssertionError((method,path))


class OfflineControls(unittest.TestCase):
    def test_official_schema_and_no_legacy_or_jupyter_fields(self):
        schema=json.loads((HERE/"official-create-schema.json").read_text())
        validator=Draft202012Validator(schema)
        for flavor in c.FLAVORS:
            body=c.create_body(flavor,"ideas-20261018-cpu-api-v2-0123456789abcdef",c.public_source(COMMIT),"SYNTHETIC-HTTP-NONCE-"*3)
            self.assertEqual(list(validator.iter_errors(body)),[])
            self.assertNotIn("gpu",body); self.assertFalse(body["startJupyter"])
            invalid=deepcopy(body); invalid["cpu"]["memory"]=256
            self.assertTrue(list(validator.iter_errors(invalid)))
            invalid=deepcopy(body); invalid["computeType"]="CPU"
            self.assertTrue(list(validator.iter_errors(invalid)))

    def test_local_payload_and_plan_need_no_provider_key_or_network(self):
        with patch.dict("os.environ",{},clear=True),patch.object(c.urllib.request,"urlopen",side_effect=AssertionError("network forbidden")),redirect_stdout(io.StringIO()) as out,patch.object(sys,"argv",[str(SCRIPT),"plan","--source-commit",COMMIT]):
            c.main()
        planned=json.loads(out.getvalue())
        self.assertIs(planned["provider_actions"],False)
        self.assertEqual(planned["payload_sha256"],c.PAYLOAD_SHA256)

    def test_api204_and_redirects_do_not_forward_authorization(self):
        response=MagicMock(); response.__enter__.return_value=response
        response.status=204; response.read.return_value=b""
        with patch.object(c,"authenticated_open",return_value=response) as opened:
            status,data=c.ApiClient("SYNTHETIC-NOT-A-CREDENTIAL").call("DELETE","/pods/ownedPod123")
        self.assertEqual((status,data),(204,None))
        self.assertEqual(opened.call_args.args[0].full_url,"https://api.runpod.io/v2/pods/ownedPod123")
        self.assertIsNone(c.NoRedirect().redirect_request(None,None,302,"redirect",{},"https://unrelated.invalid"))

    def test_complete_pagination_and_repeating_cursor_rejection(self):
        client=MagicMock()
        client.call.side_effect=[(200,dict(pods=[],pagination=dict(hasNextPage=True,nextCursor="opaque /+"))),
            (200,dict(pods=[dict(id="own",name="exact")],pagination=dict(hasNextPage=False,nextCursor=None)))]
        self.assertEqual(c.named_pods(client,"exact"),[dict(id="own",name="exact")])
        self.assertIn("cursor=opaque%20%2F%2B",client.call.call_args.args[1])
        client.call.side_effect=[(200,dict(pods=[],pagination=dict(hasNextPage=True,nextCursor="x")))]*2
        with self.assertRaises(ValueError):
            c.named_pods(client,"exact")

    def run_mock(self,client,directory):
        def armed(*args):
            client.events.append("watchdog_armed")
        with patch.dict("os.environ",{"RUNPOD_API_KEY":"SYNTHETIC-NOT-A-CREDENTIAL"},clear=True),patch.object(c,"prove_public_source",return_value=dict(sha256=c.PAYLOAD_SHA256,authorization_header_supplied=False)),patch.object(c,"start_watchdog",side_effect=armed),patch.object(c,"fetch_job",return_value=dict(results_fetched=True,workflow_returncode=0)),redirect_stdout(io.StringIO()):
            return c.execute(COMMIT,directory,client_factory=lambda *a,**k:client)

    def test_400_and403_fallbacks_preserve_separate_attempts(self):
        for refused in (400,403):
            with self.subTest(status=refused),tempfile.TemporaryDirectory() as temporary:
                directory=Path(temporary)/"fresh"; client=FakeClient(failures=[refused])
                self.run_mock(client,directory)
                self.assertEqual([b["cpu"]["id"] for b in client.created],["cpu3m","cpu5m"])
                self.assertLess(client.events.index("watchdog_armed"),client.events.index("post"))
                self.assertTrue((directory/"allocation-1-cpu3m/refusal.json").is_file())
                self.assertEqual(client.deleted,["/pods/ownedPod123"])
                all_text="".join(p.read_text() for p in directory.rglob("*") if p.is_file())
                self.assertNotIn("SYNTHETIC-NOT-A-CREDENTIAL",all_text)
                self.assertNotIn(client.created[-1]["env"]["IDEAS_HTTP_BEARER"],all_text)
                with self.assertRaises(FileExistsError):
                    self.run_mock(client,directory)

    def test_500_ambiguous_stops_without_second_post(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/"fresh"; client=FakeClient(failures=[500])
            with self.assertRaises(RuntimeError):
                self.run_mock(client,directory)
            self.assertEqual(len(client.created),1)
            self.assertTrue((directory/"ownership-intent.json").is_file())
            self.assertTrue((directory/"cleanup-requested.json").is_file())
            self.assertEqual(client.events[:2],["watchdog_armed","post"])

    def test_wrong_creation_status_and_guard_failures_cleanup_exact_id(self):
        cases=[(202,{}),(201,dict(name="unexpected")),(201,dict(cost=2.11)),
            (201,dict(cost=float("nan"))),(201,dict(cpu=dict(id="cpu3m",vcpuCount=32,memory=255)))]
        for status,change in cases:
            with self.subTest(status=status,change=change),tempfile.TemporaryDirectory() as temporary:
                client=FakeClient(change=change,status=status)
                with self.assertRaises((ValueError,RuntimeError)):
                    self.run_mock(client,Path(temporary)/"fresh")
                self.assertEqual(client.deleted,["/pods/ownedPod123"])

    def test_catalog_and_ownership_fail_closed(self):
        client=FakeClient(); status,body=client.call("GET","/catalog/cpus")
        for bad in (True,float("nan"),-1,1):
            with self.subTest(bad=bad):
                changed=deepcopy(body); changed["cpus"][0]["ramGbPerVcpu"]=bad
                with patch.object(client,"call",return_value=(status,changed)),self.assertRaises(ValueError):
                    c.selected_catalog(client)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"owner.json"
            path.write_text(json.dumps(dict(schema=c.ARTIFACT_VERSION,api_base=c.API,id="ownedPod123",
                name="ideas-20261018-cpu-api-v2-0123456789abcdef",maximum_seconds=2701,started_unix=0,
                expires_unix=2701,delete_url=c.API+"/pods/ownedPod123")))
            with self.assertRaises(ValueError):
                c.ownership(path)

    def test_cleanup_retries_transient_failure_until_exact_absence(self):
        client=MagicMock(); client.call.side_effect=[c.ProviderError(500,"transient"),(204,None),c.ProviderError(404,"absent")]
        with tempfile.TemporaryDirectory() as temporary,patch.object(c.time,"sleep"):
            result=c.cleanup_until_absent(client,dict(id="ownedPod123",expires_unix=10**12),Path(temporary))
            self.assertTrue(result["absence_verified"])
            self.assertEqual(client.call.call_args.args,("GET","/pods/ownedPod123"))

    def test_cleanup_survives_log_disk_failure_and_atomic_no_overwrite(self):
        client=MagicMock(); client.call.side_effect=[c.ProviderError(500,"transient"),(204,None),c.ProviderError(404,"absent")]
        with tempfile.TemporaryDirectory() as temporary,patch.object(c.time,"sleep"),patch.object(c,"write_once",side_effect=OSError("synthetic ENOSPC")):
            self.assertTrue(c.cleanup_until_absent(client,dict(id="ownedPod123",expires_unix=10**12),Path(temporary))["absence_verified"])
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"atomic.json"
            c.write_once(path,{"complete":True})
            with self.assertRaises(FileExistsError):
                c.write_once(path,{"overwrite":True})
            self.assertEqual(json.loads(path.read_text()),{"complete":True})

    def test_failed_watchdog_start_blocks_every_post(self):
        with tempfile.TemporaryDirectory() as temporary:
            client=FakeClient()
            with patch.dict("os.environ",{"RUNPOD_API_KEY":"SYNTHETIC-NOT-A-CREDENTIAL"},clear=True),patch.object(c,"prove_public_source",return_value=dict(sha256=c.PAYLOAD_SHA256)),patch.object(c,"start_watchdog",side_effect=RuntimeError("synthetic child startup failure")):
                with self.assertRaises(RuntimeError):
                    c.execute(COMMIT,Path(temporary)/"fresh",client_factory=lambda *a,**k:client)
            self.assertEqual(client.created,[])

    def test_prepost_intent_watchdog_handles_late_visibility(self):
        bearer="SYNTHETIC-FRESH-HTTP-BEARER-"*3
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"ownership-intent.json"
            path.write_text(json.dumps(dict(schema=c.ARTIFACT_VERSION+"/intent",api_base=c.API,
                name="ideas-20261018-cpu-api-v2-0123456789abcdef",started_unix=0,expires_unix=2700,maximum_seconds=2700,
                http_bearer_sha256=hashlib.sha256(bearer.encode()).hexdigest())))
            # A parent crash must not make a partial ownership file block nonce cleanup.
            (Path(temporary)/"ownership.json").write_text('{"partial":')
            pod=dict(id="lateOwned123",env=dict(IDEAS_HTTP_BEARER=bearer))
            with patch.object(c.time,"time",return_value=2400),patch.object(c.time,"sleep"),patch.object(c,"named_pods",side_effect=[[],[pod]]),patch.object(c,"cleanup_until_absent",return_value=dict(id="lateOwned123",absence_verified=True)) as cleanup:
                c.intent_watchdog(path,MagicMock(),bearer)
            self.assertEqual(cleanup.call_args.args[1]["id"],"lateOwned123")
            self.assertTrue((Path(temporary)/"intent-watchdog-cleanup.json").is_file())


if __name__=="__main__":
    unittest.main(verbosity=2)
