"""Keep withdrawn recommendations out of the live catalog without erasing history."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_catalog.py'


class CatalogWithdrawalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(SCRIPT, self.root / 'scripts/build_catalog.py')
        self.dest = self.root / 'research/catalog'
        self.dest.mkdir(parents=True)
        self.write('research/catalog/sources.json', {'sources': [
            {'path': 'source.json', 'array': 'items', 'status': 'discussion_candidate'}
        ]})
        self.write('research/catalog/classification.json', {
            'worlds': [{'id': 'S3', 'title': '科学与计算', 'description': '可追溯关系'}],
            'names': {name: {'primary': 'S3', 'tags': [], 'reason': 'fixture'}
                      for name in ['首名', '次名', '新名']}
        })
        self.rows = [self.row('first', '首名'), self.row('second', '次名')]
        self.write('source.json', {'items': self.rows})

    def write(self, path, data):
        (self.root / path).write_text(json.dumps(data, ensure_ascii=False))

    @staticmethod
    def row(family, name):
        return {
            'family_id': family, 'chinese': name, 'english': family,
            'source': {'title': 'source', 'url': 'https://example.com/'},
            'meaning': 'meaning', 'crossing': 'relation', 'layers': [],
            'chinese_screen': {'decision': 'public_use_screen_pass'},
            'english_screen': {'decision': 'public_use_screen_pass'}
        }

    def build(self, success=True):
        result = subprocess.run(['python3', str(self.root / 'scripts/build_catalog.py')],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def withdraw(self):
        self.write('proof.json', {'decision': 'existing_company'})
        digest = hashlib.sha256((self.root / 'proof.json').read_bytes()).hexdigest()
        self.write('research/catalog/revisions.json', {'entries': [{
            'family_id': 'first', 'previous_status': 'discussion_candidate',
            'status': 'withdrawn', 'reviewer': 'reviewer', 'reviewed_at': '2026-11-07',
            'reason': 'new evidence',
            'review_refs': [{'path': 'proof.json', 'sha256': digest}]
        }]})

    def test_withdrawal_preserves_id_and_history_but_excludes_live_counts(self):
        self.build()
        old_ids = json.loads((self.dest / 'ids.json').read_text())
        self.withdraw()
        self.rows.append(self.row('third', '新名'))
        self.write('source.json', {'items': self.rows})
        self.build()
        catalog = json.loads((self.dest / 'catalog.json').read_text())
        self.assertEqual(catalog['counts']['discussion_candidates'], 2)
        self.assertEqual(catalog['counts']['total_unique_families'], 2)
        self.assertEqual(catalog['counts']['withdrawn_families'], 1)
        self.assertEqual(catalog['counts']['historical_unique_families'], 3)
        entries = {x['family_id']: x for x in catalog['entries']}
        self.assertEqual(entries['first']['status'], 'withdrawn')
        self.assertEqual(entries['first']['id'], old_ids['first'])
        self.assertEqual(entries['second']['id'], old_ids['second'])
        self.assertNotIn(entries['third']['id'], old_ids.values())
        readme = (self.dest / 'README.md').read_text()
        active, withdrawn = readme.split('## 已撤回，非备选')
        self.assertNotIn('[**首名**]', active)
        self.assertIn('首名 / first', withdrawn)
        before = (self.dest / 'catalog.json').read_bytes()
        self.build()
        self.assertEqual((self.dest / 'catalog.json').read_bytes(), before)

    def test_changed_withdrawal_evidence_blocks_rebuild(self):
        self.build()
        self.withdraw()
        self.write('proof.json', {'decision': 'changed_without_reacceptance'})
        result = self.build(success=False)
        self.assertIn('revision evidence changed', result.stderr)


if __name__ == '__main__':
    unittest.main()
