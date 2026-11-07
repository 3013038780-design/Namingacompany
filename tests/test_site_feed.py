import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_feed', ROOT / 'scripts/build_site_feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


class SiteFeedTests(unittest.TestCase):
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
        admitted_ids = {e['origin_chinese_id'] for e in data['entries'] if e['status'] == 'discussion_candidate'}
        self.assertTrue(admitted_ids.isdisjoint({e['chinese_id'] for e in data['pending_evidence']}))
        self.assertEqual(sum(e['status'] == 'discussion_candidate' for e in data['entries']), data['counts']['discussion_candidates'])
        self.assertNotIn('raw_search_results', json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
