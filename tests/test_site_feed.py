import importlib.util
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_feed', ROOT / 'scripts/build_site_feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


class SiteFeedTests(unittest.TestCase):
    def test_changing_active_run_keeps_prior_daily_history(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            def put(path, value):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(value))
            put('research/catalog/catalog.json', {'counts': {}, 'entries': [], 'worlds': []})
            put('research/runs/2026-11-07-continuous-001/progress.json', {'updated_at': None})
            for number in (1, 2):
                base = f'research/runs/round{number}/continuations/checkpoint'
                put(base + '/decisions-through-batch1.json', {'updated_at': f'2026-11-0{number}T12:00:00+08:00',
                    'items': [{'chinese_id': f'C{number}', 'chinese': f'name{number}', 'reason': 'evidence', 'status': 'hold'}]})
                put(base + '/result.json', {'completed_at': f'2026-11-0{number}T12:00:00+08:00'})
            put('research/continuation-queue.json', {'active_run': 'research/runs/round2',
                'latest_frozen_decision_snapshot': 'research/runs/round2/continuations/checkpoint/decisions-through-batch1.json',
                'scheduler': {'status': 'ACTIVE', 'cadence': 'hourly'}})
            with patch.object(feed, 'ROOT', root):
                data = feed.build()
            self.assertEqual(len(data['events']), 2)
            self.assertEqual({e['chinese'] for e in data['research']}, {'name1', 'name2'})

    def test_public_queries_do_not_export_raw_source_payloads(self):
        compact = feed.screen({'query_logs': [{'query': 'example', 'summary': 'A result',
                                               'raw_search_results': 'full third-party text',
                                               'private_preservation_path': '/private/file'}]})
        self.assertEqual(compact['queries'], [{'query': 'example', 'summary': 'A result'}])

    def test_website_admission_counts_and_pending_stay_separate(self):
        data = json.loads((ROOT / 'research/catalog/website.json').read_text())
        canonical = json.loads((ROOT / 'research/catalog/catalog.json').read_text())
        self.assertEqual(data['counts'], canonical['counts'])
        self.assertEqual({e['id'] for e in data['entries']}, {e['id'] for e in canonical['entries']})
        admitted_pairs = {(e['chinese'], e['english']) for e in data['entries'] if e['status'] == 'discussion_candidate'}
        self.assertTrue(admitted_pairs.isdisjoint({(e['chinese'], e['english']) for e in data['pending_evidence']}))
        self.assertEqual(sum(e['status'] == 'discussion_candidate' for e in data['entries']), data['counts']['discussion_candidates'])
        self.assertNotIn('raw_search_results', json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
