"""Copy the transitive official request-schema closure; no API access."""
from pathlib import Path
import hashlib
import json

root=Path(__file__).resolve().parent
source=Path("/tmp/ideas-runpod-v2-openapi.json")
document=json.loads(source.read_text())
selected={}; todo=["CreatePodRequest"]
def references(value):
    if isinstance(value,dict):
        ref=value.get("$ref","")
        if ref:
            if not ref.startswith("#/components/schemas/"):
                raise ValueError("nonlocal schema reference")
            yield ref.split("/")[-1]
        for child in value.values():
            yield from references(child)
    elif isinstance(value,list):
        for child in value:
            yield from references(child)
while todo:
    name=todo.pop()
    if name in selected:
        continue
    selected[name]=document["components"]["schemas"][name]
    todo.extend(references(selected[name]))
schema={"$schema":"https://json-schema.org/draft/2020-12/schema",
    "$ref":"#/components/schemas/CreatePodRequest","components":{"schemas":selected}}
with (root/"official-create-schema.json").open("x") as output:
    output.write(json.dumps(schema,indent=2,sort_keys=True)+"\n")
provenance={"input":str(source),"input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
    "input_openapi_version":document["openapi"],"schema_names":sorted(selected),
    "retrieval":"Root-provided official local OpenAPI snapshot; this task performed no network retrieval",
    "post_url":"https://api.runpod.io/v2/pods"}
with (root/"schema-provenance.json").open("x") as output:
    output.write(json.dumps(provenance,indent=2,sort_keys=True)+"\n")
print(json.dumps({"schema_count":len(selected),"input_sha256":provenance["input_sha256"]}))
