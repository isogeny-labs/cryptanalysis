import copy
import json
import unittest
import ct197_native_evidence as e

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = []
        raw = []
        labels = (0,1,2,17,12345,2771710)
        for from_, to in ((0,2),(2,0)):
            for sector in range(4):
                for scalar in labels:
                    fixture.append({'from':from_,'to':to,'sector':sector,'scalar_OUTSIDE_runtime':scalar})
        for i, row in enumerate(fixture):
            for route in e.ROUTES:
                panels = []
                for panel in ('original','control'):
                    slots = []
                    for block in range(16):
                        for slot, arm in enumerate(e.expected_order(panel,block)):
                            # Synthetic oracle only, not native pricing.
                            ns = (110 if arm=='N2_actual' else 100)*64
                            slots.append({'block':block,'slot':slot,'arm':arm,
                                'recorded':block>=4,'repetitions':64,'raw_slot_ns_decimal':str(ns)})
                    panels.append(slots)
                raw.append({'packet_index':i,'from':row['from'],'to':row['to'],
                    'sector':row['sector'],'scalar_label_outside_runtime':row['scalar_OUTSIDE_runtime'],
                    'physical_transfer_route':route,'raw_slots':panels[0],
                    'counter_control_slots':panels[1],
                    'observed_actual_norm_calls_original_panel':2048,
                    'observed_actual_norm_calls_counter_control_panel':2048})
        cls.fixture = fixture
        cls.good = dict(schema=e.SCHEMA,parent_schema='ct192-public48-actual-norm-price/v1',
            standing='[pcc:unverified]',scope='same-process price; no complete ECDLP',
            source_git_blob=e.SOURCE_BLOB,fixture_git_blob=e.FIXTURE_BLOB,
            source_prime=223,source_group_prime=2771711,admission_producer_asserted_only=True,
            public_packets=48,true_route_operands=96,original_recorded_slots=4608,
            extra_counter_control_recorded_slots=4608,observed_actual_norm_calls_total=393216,
            same_process_setup_ns_decimal='10000',in_process_total_ns_decimal='200000000',
            peak_rss_kib_linux=None,target_arch='x86_64',target_os='linux',raw_operands=raw,
            complete_single_target_ecdlp_solved=False)

    def test_accepted_synthetic_scoped_only(self):
        report = e.adjudicate(self.good, self.fixture)
        self.assertEqual(report['raw_operands'],96)
        self.assertEqual(len(report['strata']),64)
        self.assertFalse(report['independent_pcc'])
        self.assertFalse(report['complete_single_target_ecdlp_solved'])
        self.assertTrue(all(abs(x['packet_ratio_median']-1.1)<1e-12 for x in report['strata']))
        self.assertEqual({x['packets'] for x in report['strata']}, {1,5})

    def test_duplicate_json_key_and_nan_rejected(self):
        for text in (b'{"x":1,"x":2}',b'{"foo":NaN}',b'{"foo":Infinity}'):
            with self.subTest(text=text),self.assertRaises(e.EvidenceError):e.load_strict(text)

    def test_roster_and_metadata_mutations_rejected(self):
        for label, f in (
            ('truncated',lambda d:d['raw_operands'].pop()),
            ('duplicate',lambda d:d['raw_operands'].__setitem__(1,copy.deepcopy(d['raw_operands'][0]))),
            ('route',lambda d:d['raw_operands'][0].__setitem__('physical_transfer_route','direct_composite_wrong')),
            ('direction',lambda d:d['raw_operands'][0].__setitem__('from',2)),
            ('extra',lambda d:d.__setitem__('unexpected',1)),
            ('false solve',lambda d:d.__setitem__('complete_single_target_ecdlp_solved',True)),
            ('fake standing',lambda d:d.__setitem__('standing','[pcc:verified]')),
            ('counter',lambda d:d['raw_operands'][0].__setitem__('observed_actual_norm_calls_original_panel',2047)),
            ('aggregate',lambda d:d.__setitem__('observed_actual_norm_calls_total',1)),
            ('time',lambda d:d.__setitem__('in_process_total_ns_decimal','100000')),
            ('missing memory',lambda d:d.__delitem__('peak_rss_kib_linux')),
        ):
            with self.subTest(label=label):
                d=copy.deepcopy(self.good);f(d)
                with self.assertRaises(e.EvidenceError):e.adjudicate(d,self.fixture)

    def test_timing_slot_mutations_rejected(self):
        changes=(('swap treatment','arm','D_padd'),('wrong period','block',3),
            ('warmup leakage','recorded',True),('repetitions','repetitions',63),
            ('float nanoseconds','raw_slot_ns_decimal','1.25'),
            ('zero nanoseconds','raw_slot_ns_decimal','0'),
            ('negative','raw_slot_ns_decimal','-10'))
        for label,field,value in changes:
            with self.subTest(label=label):
                d=copy.deepcopy(self.good);d['raw_operands'][0]['raw_slots'][0][field]=value
                with self.assertRaises(e.EvidenceError):e.adjudicate(d,self.fixture)

    def test_source_fixture_not_derived_from_producer(self):
        d=copy.deepcopy(self.good)
        fixture=copy.deepcopy(self.fixture)
        fixture[0]['scalar_OUTSIDE_runtime']=2
        with self.assertRaises(e.EvidenceError):e.adjudicate(d,fixture)

if __name__=='__main__': unittest.main()
