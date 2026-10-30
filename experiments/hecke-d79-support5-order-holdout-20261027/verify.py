"""Cross-link frozen stage receipts and terminal scientific status."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text())


def digest(name):
    return hashlib.sha256((HERE/name).read_bytes()).hexdigest()


def main():
    pre=read('pre_class.json')
    cls=read('post_class.json')
    source=read('post_source.json')
    analysis=read('post_analysis.json')
    analysis_v2=read('post_analysis_v2.json')
    result=read('post_result.json')
    audit=read('post_audit.json')
    assert pre['inputs_sha256']==digest('inputs.json')
    assert pre['prescreen_sha256']==digest('prescreen.json')
    assert pre['class_producer_sha256']==digest('class_producer.py')
    aliases={'inputs':'inputs.json',
             'prescreen':'prescreen.json',
             'class_result':'class-result.json',
             'source_result':'source-result.json',
             'analysis':'analysis.json',
             'source_producer':'source_producer.py',
             'analyze':'analyze.py'}
    for receipt in (cls,source,analysis,analysis_v2,result,audit):
        for name,sha in receipt['sha256'].items():
            assert digest(aliases.get(name,name))==sha,(name,sha)
    assert read('prescreen.json')['status']=='COMPLETE'
    assert read('class-result.json')['cases'][0]['status']=='CLASS_READY'
    assert read('source-result.json')['cases'][0]['status']=='COMPLETE'
    assert read('analysis.json')['cases'][0]['status']=='COMPLETE'
    assert read('result.json')['status']=='COMPLETE'
    assert read('audit-support4.json')['status']=='PASS'
    assert read('audit-support5.json')['status']=='PASS'
    assert read('result.json')['paths']['ascending']['first_rank40']=={
        'support4':26,'support4_plus_direct5':0}
    assert read('result.json')['paths']['priority']['first_rank40']=={
        'support4':29,'support4_plus_direct5':0}
    build=(HERE/'formal/build-output.txt').read_text()
    assert 'Build completed successfully' in build and 'error:' not in build
    print('PASS: frozen stage receipts, results, audits, and Lean build')


if __name__=='__main__':
    main()
