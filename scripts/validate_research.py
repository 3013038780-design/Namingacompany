"""Validate recorded counts, candidate references and screening provenance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(run):
    data = {p.stem: json.loads(p.read_text()) for p in run.glob('*.json')}
    candidates = data['candidates']['candidates']
    by_id = {c['id']: c for c in candidates}
    assert len(by_id) == len(candidates), f'{run}: duplicate candidate IDs'
    materials = {m['id'] for m in data['materials']['materials']}
    for c in candidates:
        assert c['name'] and c['meaning'] and c['source_urls'], c['id']
        assert set(c['material_ids']) <= materials, c['id']
    if 'final' not in data:
        assert data['run']['stage'] == 'chinese_review', 'incomplete run needs explicit stage'
        assert data['run']['current_shortlisted_pairs'] == 0
        assert data['candidates']['candidate_count'] == len(candidates)
        assert len({c['family_id'] for c in candidates}) == data['candidates']['family_count']
        assert all(c['new_recommendation'] is False for c in candidates)
        print(f'{run.name}: Chinese research drafts only; counts/references valid, not final recommendations')
        return
    counts = data['final']['counts']
    assert counts['cases'] == len(data['cases']['cases'])
    assert counts['materials'] == len(materials)
    assert counts['raw_word_forms'] == len(candidates)
    editorial = {r['id']: r for r in data['editorial']['rows']}
    assert set(editorial) == set(by_id)
    assert counts['conservative_families'] == len({r['family_id'] for r in editorial.values()})
    assert counts['editorial_rejected_forms'] == sum(r['decision'] == 'editorial_reject' for r in editorial.values())
    assert counts['chinese_screened_forms'] == len(data['screening']['candidates'])
    checks = {r['name']: r for r in data['screening']['english_checks']}
    pairs = data['final']['pairs']
    assert counts['complete_discussion_pairs'] == len(pairs)
    families = set()
    for pair in pairs:
        assert by_id[pair['id']]['name'] == pair['chinese']
        assert checks[pair['english']]['status'].startswith('preliminary_clear')
        family = editorial[pair['id']]['family_id']
        assert family not in families, 'same family counted twice'
        families.add(family)
    assert data['run']['actual_counts'] == counts
    assert data['run']['schedule_created'] is False
    for p in run.glob('*.json'):
        assert '/Users/' not in p.read_text(), f'local path leaked: {p.name}'
    print(f'{run.name}: {len(candidates)} forms, {len(families)} discussion pairs; provenance/count checks passed')


if __name__ == '__main__':
    runs = sorted((ROOT / 'research' / 'runs').iterdir())
    for run in runs:
        if run.is_dir():
            validate(run)
