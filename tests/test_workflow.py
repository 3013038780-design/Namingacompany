"""Synthetic protocol fixtures only: no real research or execution claims."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_workflow import CONTRACT, validate


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / 'synthetic-run'
        self.run.mkdir()
        self.fixture()

    def put(self, name, data):
        (self.run / name).write_text(json.dumps(data, ensure_ascii=False))

    def get(self, name):
        return json.loads((self.run / name).read_text())

    def refresh_hashes(self):
        h = self.get('handoffs.json')
        for row in h['handoffs']:
            for ref in row['input_refs'] + row['output_refs']:
                ref['sha256'] = hashlib.sha256((self.run / ref['path']).read_bytes()).hexdigest()
        self.put('handoffs.json', h)

    def fixture(self, zero=False):
        roles = {r: {'agent_id': 'synthetic-' + r, 'execution_ref': 'synthetic-tool-' + r,
                     'status': 'completed', 'started_at': '2026-11-06T06:00:00+08:00',
                     'completed_at': '2026-11-06T06:01:00+08:00'} for r in CONTRACT['roles']}
        self.put('run.json', {'protocol_version': '1.0', 'run_id': self.run.name,
                            'date': '2026-11-06', 'research_mode': 'bootstrap',
                            'coordinator_id': 'synthetic-root', 'roles': roles,
                            'status': 'complete_without_candidates' if zero else 'complete_with_candidates'})
        cases = [{'id': f'K{i}', 'category': CONTRACT['case_categories'][i // 4],
                  'name': f'Synthetic case {i}', 'word_origin_fact': 'synthetic fact',
                  'naming_analysis': 'synthetic interpretation', 'reading_scope': 'synthetic body',
                  'sources': [{'url': 'https://example.invalid/case', 'access': 'body', 'supports': 'synthetic fact'}]} for i in range(12)]
        principles = [{'id': f'P{i}', 'positive_example': 'positive fixture',
                       'counterexample': 'negative fixture', 'boundary': 'fixture boundary'} for i in range(6)]
        self.put('cases.json', {'cases': cases, 'principles': principles, 'counterexamples': ['x', 'y', 'z']})
        materials = [{'id': f'M{i}', 'family_id': f'MF{i}', 'category': f'category-{i % 6}',
                      'reading_scope': 'chapter', 'reading_location': 'synthetic paragraph',
                      'source_urls': ['https://example.invalid/material'], 'fact': 'synthetic fact',
                      'source_type': 'book' if i < 2 else ('news' if i < 5 else 'other'),
                      'book_id': f'B{i}', 'published_at': '2026-11-01', 'is_classical': False} for i in range(24)]
        self.put('materials.json', {'materials': materials})
        candidates = [{'id': f'C{i}', 'name': f'测试名{i}', 'family_id': f'F{i}',
                       'material_ids': [f'M{i}'], 'principle_ids': [f'P{i % 6}'],
                       'meaning': 'synthetic meaning', 'combination_reason': 'synthetic relation',
                       'weakness': 'synthetic weakness', 'history_check': {'status': 'new', 'reason': 'synthetic history check'}} for i in range(24)]
        self.put('candidates.json', {'candidates': candidates})
        reviews = []
        if not zero:
            for language, name in [('zh', '测试名0'), ('en', 'SyntheticName')]:
                for reviewer in ['producer', 'coordinator']:
                    axes = CONTRACT['score_minimum'][language]
                    reviews.append({'candidate_id': 'C0', 'language': language, 'name': name,
                                    'reviewer': reviewer, 'execution_ref': 'synthetic-review-tool',
                                    'independent_submission_ref': language + reviewer,
                                    'scores': {a: 5 for a in axes},
                                    'notes': {a: {'reason': 'synthetic editorial reason', 'counter_association': 'synthetic counterexample'} for a in axes}})
        self.put('quality.json', {'reviews': reviews})
        registry = [{'region': region, 'type': kind, 'status': 'unavailable',
                     'url': 'https://example.invalid/registry', 'attempted_at': '2026-11-06',
                     'detail': 'synthetic unavailable registry fixture'} for region, kind in
                    [('CN', 'company'), ('CN', 'trademark_9'), ('CN', 'trademark_42'), ('UK', 'company')]]
        def screen(language, name):
            return {'candidate_id': 'C0', 'name': name, 'status': 'pass_public_precheck',
                    'queries': [{'kind': k, 'query': f'synthetic {language} query {i}',
                                 'executed_at': '2026-11-06', 'result_summary': 'synthetic no-match fixture', 'evidence': []}
                                for i, k in enumerate(CONTRACT['query_kinds'][language])],
                    'registry_checks': registry}
        self.put('screening.json', {'chinese': [] if zero else [screen('zh', '测试名0')],
                                    'english': [] if zero else [screen('en', 'SyntheticName')],
                                    'positive_controls': [{'entity_type': t, 'detected': True, 'url': 'https://example.invalid/control'} for t in ['company', 'product']]})
        self.put('english.json', {'entries': [] if zero else [{'candidate_id': 'C0', 'name': 'SyntheticName', 'status': 'selected'}]})
        self.put('final.json', {'candidates': [] if zero else [{'id': 'C0', 'family_id': 'F0', 'chinese': '测试名0', 'english': 'SyntheticName', 'source_ids': ['M0']}]})
        self.put('rejections.json', {'entries': [{'candidate_id': f'C{i}', 'name': f'测试名{i}',
                                                'language': 'zh', 'stage': 'editorial', 'reason_code': 'BRAND_FIT',
                                                'reason': 'synthetic rejection, not a real brand judgment', 'evidence': []}
                                               for i in range(0 if zero else 1, 24)]})
        (self.run / 'README.md').write_text('Synthetic test fixture, not actual research.')
        endpoints = [('A1', 'A2'), ('A2', 'coordinator'), ('coordinator', 'A3'),
                     ('A3', 'A4'), ('A4', 'A3'), ('A3', 'coordinator'), ('coordinator', 'user')]
        handoffs = []
        for i, hid in enumerate(CONTRACT['handoffs']):
            ids = [] if hid == 'H1' else ([f'C{j}' for j in range(24)] if hid == 'H2' else ([] if zero else ['C0']))
            outputs = [{'path': f, 'sha256': ''} for f in CONTRACT['handoff_output_files'][hid]]
            handoffs.append({'id': hid, 'from': endpoints[i][0], 'to': endpoints[i][1],
                             'timestamp': f'2026-11-06T06:{10+i:02d}:00+08:00',
                             'status': 'zero_input' if zero and hid not in ['H1', 'H2'] else 'accepted',
                             'reason': 'synthetic zero-input or accepted fixture', 'candidate_ids': ids,
                             'input_refs': [{'path': 'cases.json', 'sha256': ''}], 'output_refs': outputs})
        self.put('handoffs.json', {'handoffs': handoffs})
        self.refresh_hashes()

    def test_valid_complete_run(self):
        self.assertIn('FORMAL CHECKS PASSED', validate(self.run))

    def test_real_zero_input_path_still_requires_all_roles(self):
        self.fixture(zero=True)
        self.assertIn('0 pairs', validate(self.run))
        m = self.get('run.json'); del m['roles']['A4']; self.put('run.json', m)
        with self.assertRaisesRegex(ValueError, 'all four roles'):
            validate(self.run)

    def test_cannot_merge_two_roles(self):
        m = self.get('run.json'); m['roles']['A2']['agent_id'] = m['roles']['A1']['agent_id']; self.put('run.json', m)
        with self.assertRaisesRegex(ValueError, 'must be distinct'):
            validate(self.run)

    def test_cannot_skip_english_handoff(self):
        h = self.get('handoffs.json'); h['handoffs'] = [x for x in h['handoffs'] if x['id'] != 'H5']; self.put('handoffs.json', h)
        with self.assertRaisesRegex(ValueError, 'missing accepted'):
            validate(self.run)

    def test_later_return_invalidates_old_acceptance(self):
        h = self.get('handoffs.json')
        returned = dict(h['handoffs'][4], status='returned', timestamp='2026-11-06T07:00:00+08:00')
        h['handoffs'].append(returned); self.put('handoffs.json', h)
        with self.assertRaisesRegex(ValueError, 'missing accepted'):
            validate(self.run)

    def test_duplicate_rework_attempt_cannot_bypass_limit(self):
        ref = {'path': 'cases.json', 'sha256': hashlib.sha256((self.run / 'cases.json').read_bytes()).hexdigest()}
        entry = {'candidate_id': 'C0', 'language': 'zh', 'attempt': 1,
                 'reason': 'synthetic rework', 'responsible_role': 'A2',
                 'before_refs': [ref], 'after_refs': [ref]}
        self.put('rework.json', {'entries': [entry, entry]})
        with self.assertRaisesRegex(ValueError, 'duplicate rework attempt'):
            validate(self.run)

    def test_third_rework_is_blocked(self):
        self.put('rework.json', {'entries': [{'candidate_id': 'C0', 'language': 'zh', 'attempt': 3}]})
        with self.assertRaisesRegex(ValueError, 'rework limit exceeded'):
            validate(self.run)

    def test_cannot_hide_survivors_with_zero_input(self):
        h = self.get('handoffs.json'); h['handoffs'][3]['status'] = 'zero_input'; h['handoffs'][3]['candidate_ids'] = []; self.put('handoffs.json', h)
        with self.assertRaisesRegex(ValueError, 'H4 input population mismatch'):
            validate(self.run)

    def test_changed_artifact_requires_reacceptance(self):
        p = self.run / 'materials.json'; p.write_text(p.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'stale artifact hash'):
            validate(self.run)

    def test_high_total_cannot_rescue_bad_lab_fit(self):
        q = self.get('quality.json'); q['reviews'][0]['scores']['lab_fit'] = 2; self.put('quality.json', q); self.refresh_hashes()
        with self.assertRaisesRegex(ValueError, 'lab_fit below gate'):
            validate(self.run)

    def test_large_reviewer_disagreement_requires_rework(self):
        q = self.get('quality.json'); q['reviews'][0]['scores']['extension'] = 3; self.put('quality.json', q); self.refresh_hashes()
        with self.assertRaisesRegex(ValueError, 'quality disagreement'):
            validate(self.run)

    def test_duplicate_family_not_counted_twice(self):
        f = self.get('final.json'); f['candidates'].append({'id': 'C1', 'family_id': 'F0', 'chinese': '测试名1', 'english': 'AnotherName', 'source_ids': ['M1']}); self.put('final.json', f); self.refresh_hashes()
        with self.assertRaisesRegex(ValueError, 'same family counted twice'):
            validate(self.run)

    def test_occupied_rejection_needs_specific_entity(self):
        d = self.get('rejections.json'); d['entries'][0]['reason_code'] = 'EXACT_TECH_USE'; self.put('rejections.json', d); self.refresh_hashes()
        with self.assertRaisesRegex(ValueError, 'exact-use rejection needs named evidence'):
            validate(self.run)

    def test_missing_rejection_reason_blocks_completion(self):
        d = self.get('rejections.json'); d['entries'].pop(); self.put('rejections.json', d); self.refresh_hashes()
        with self.assertRaisesRegex(ValueError, 'per-name Chinese exclusion'):
            validate(self.run)

    def test_new_run_cannot_omit_protocol(self):
        m = self.get('run.json'); del m['protocol_version']; self.put('run.json', m)
        with self.assertRaisesRegex(ValueError, 'must declare protocol_version'):
            validate(self.run)

    def test_incomplete_run_cannot_publish_finalists(self):
        m = self.get('run.json'); m['status'] = 'incomplete'; self.put('run.json', m)
        with self.assertRaisesRegex(ValueError, 'incomplete run cannot advertise'):
            validate(self.run)


if __name__ == '__main__':
    unittest.main()
