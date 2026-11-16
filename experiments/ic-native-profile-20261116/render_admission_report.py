#!/usr/bin/env python3
"""Preserve the failed version-metadata admission without performance claims."""
import json,subprocess
from pathlib import Path
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image
P=Path(__file__).resolve().parent;S=json.loads((P/'profile-001/summary.json').read_text());assert S['status']=='failed_or_capped'
text='''# Instruction profile001: version-metadata admission failure

[pcc:unverified] Job20261116-114025-772f exits1 after1.7seconds. The prepared binary/receipt and fixed N27 development point are loaded, but capability preflight and all target profiles remain unexecuted. There are zero instruction captures and11raw outputs. No arithmetic or native performance conclusion follows.

[pcc:unverified] valgrind --version reports3.22.0 and exits0. callgrind_annotate --version prints callgrind_annotate-3.22.0 and exits255. The driver incorrectly requires0 for that version query and aborts. Raw stdout/stderr, commands, host snapshot, binary/receipt/calibration and failure summary remain preserved in profile-001 and the SHA/URI bundle.

Correction: VERSION_QUERY_AMENDMENT.md replaces only the annotator version query with the package version query plus tool-file hashes, and requires an explicit distinct output identifier. Frozen binary, calibration, N27 development point0, ABBA IC modes, fresh rho references, actual capability gate and all resource/stop rules remain. No cap extension or host filtering. The corrected attempt has not run at report generation.

Requested resource: one L4,4CPU,8GiB,900s; CPU profiling only. Controller780s, IC120s/rho60s/preflight90s/export20s caps, instrumentation32GiB virtual address limit. This attempt ends during metadata collection. Requested and exposed physical placement/memory/throttle/OOM remain unqualified. Profiling wall time is not native performance.

Sources: PROTOCOL.md and official Callgrind manual/platform list; exact source642353605523 and pinned native binary2e8b4e26b30756ce2910572a45642eab29def58544fbf58b71d88dde49591bdf. Claim references and custody are in the associated benchmark record and PCC ledger. Standing is unsigned producer evidence.
'''
(P/'REPORT-profile001.md').write_text(text)
(P/'admission001.dot').write_text('digraph G {rankdir=LR;node[shape=box,style="rounded"];a[label="Pinned binary / receipts"];b[label="Version query prints 3.22.0\\nexit 255"];c[label="Zero-exit assertion stops\\nNo target profiles"];d[label="Preserve failure\\nCorrect metadata query"];a->b->c->d;}')
for ext in ['png','svg']:subprocess.run(['dot','-T'+ext,str(P/'admission001.dot'),'-o',str(P/f'admission001.{ext}')],check=True)
styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=13
story=[Paragraph('Instruction profile001: admission failure',styles['Title']),Spacer(1,10)]
for paragraph in text.split('\n\n')[1:]:story += [Paragraph(paragraph.replace('&','&amp;').replace('<','&lt;'),styles['BodyText']),Spacer(1,12)]
story += [Image(str(P/'admission001.png'),width=493,height=70,kind='proportional')]
SimpleDocTemplate(str(P/'REPORT-profile001.pdf'),leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=36).build(story)
