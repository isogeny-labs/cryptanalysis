"""Render the software-accounting report. No benchmark or curve experiment."""
from pathlib import Path
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
HERE = Path(__file__).resolve().parent
fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('off')
boxes = [('Public source target', .02), ('Cold setup + maps', .27), ('Solver + source check', .52), ('Fixed-arm cohort sum', .77)]
for label, x in boxes:
    ax.text(x+.105, .6, '\n'.join(textwrap.wrap(label, 18)), ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='#e7eff8', edgecolor='#2c5274'), transform=ax.transAxes)
for x in (.23, .48, .73):
    ax.annotate('', xy=(x+.045,.6), xytext=(x-.015,.6), xycoords='axes fraction',
                arrowprops=dict(arrowstyle='->', color='#2c5274'))
ax.text(.5,.25,'All phases explicit; unknown costs reject the comparison.\nAccounting only: arithmetic, provenance and execution remain separate gates.',
        ha='center', transform=ax.transAxes, fontsize=12)
fig.savefig(HERE/'accounting.svg', bbox_inches='tight')
with PdfPages(HERE/'REPORT.pdf') as pdf:
    page = plt.figure(figsize=(8.27,11.69))
    lines = [
        'Complete-cost transfer follow-up',
        '2026-11-15 — software development; [pcc:unverified]',
        '',
        'Scope: pursue the CM/isogeny lead after CT140 strengthened the direct-source baseline. Keep the selected 31-bit CM toy subgroup separate from the original-prime 695/701 Jacobian chain.',
        '',
        'Implementation: cold_cost_audit.py requires every setup, generator, target-transport, solver and original-source verification phase. It rejects missing or nested phases, wrong units, incomplete/failed panels, missing memory and source/binary digests. Selection is one fixed arm over the cohort, never one arm per target.',
        '',
        'Development checks: 18 synthetic unit tests passed. Guarded CT140 widths 4 and 16 now export disjoint native phase timestamps and bind them to timed rows. Both generated C++ sources compiled; neither was executed. No timing, DLP, transfer gain, provenance or signed scientific standing is established.',
        '',
        'Execution blocker: the mandatory checkpoint gate reports no AWS profile or upload token. No new transfer experiment was launched. The KB wrapper is unavailable. The shared lab contract endpoint returned unreadable VLT10 content.',
        '',
        'Next: provision checkpoint access; freeze fresh targets/protocol and exact native source; execute matched complete-cost comparisons with genuine receipts. Obtain original-prime C169/C13a/C13b/D and full-chain measurements before evaluating that separate claim.',
        '',
        'Sources: cryptanalysis PR1552; CT140_LOW_LANE_PROTOCOL.md; CT140_LOCAL_EXECUTION.md; CT139_SECOND_EXECUTION_01.md; ct136_native.cpp, base a4a75dc.',
        '',
        'No canonical curve-route fact changed. CT131_MECHANISM.svg and the CT140 scope/identities were checked; their conclusions and figures are retained.'
    ]
    y = .95
    for text in lines:
        wrapped = textwrap.wrap(text, 88) or ['']
        page.text(.08, y, '\n'.join(wrapped), va='top', fontsize=11 if y<.95 else 16)
        y -= .020*len(wrapped)+.012
    pdf.savefig(page)
    plt.close(page)
    pdf.savefig(fig)
plt.close(fig)
