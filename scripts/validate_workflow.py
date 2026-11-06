"""Check protocol records; this cannot verify real execution or editorial truth."""
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'docs/workflow-contract.json').read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(record, keys, label):
    for key in keys:
        require(key in record and record[key] not in (None, ''), f'{label}: missing {key}')


def reference(run, ref):
    fields(ref, ['path', 'sha256'], 'artifact reference')
    relative = Path(ref['path'])
    require(not relative.is_absolute(), 'artifact path must be relative')
    p = (run / relative).resolve()
    require(p.is_relative_to(run.resolve()), 'artifact escapes run directory')
    require(p.name != 'handoffs.json', 'handoff cannot hash itself')
    require(p.is_file(), f'missing artifact: {ref["path"]}')
    require(hashlib.sha256(p.read_bytes()).hexdigest() == ref['sha256'], f'stale artifact hash: {ref["path"]}')


def review_pair(reviews, candidate_id, language, name):
    selected = [r for r in reviews if (r.get('candidate_id'), r.get('language'), r.get('name')) == (candidate_id, language, name)]
    require(len(selected) == 2 and {r.get('reviewer') for r in selected} == {'producer', 'coordinator'}, f'{candidate_id}/{language}: need two distinct effective reviews')
    for r in selected:
        fields(r, ['execution_ref', 'independent_submission_ref', 'scores', 'notes'], 'quality review')
        require(set(r['scores']) == set(CONTRACT['score_minimum'][language]), 'quality axes mismatch')
        for axis, minimum in CONTRACT['score_minimum'][language].items():
            value = r['scores'][axis]
            require(type(value) is int and minimum <= value <= CONTRACT['score_max'], f'{candidate_id}/{language}: {axis} below gate')
            fields(r['notes'].get(axis, {}), ['reason', 'counter_association'], f'{candidate_id}/{axis}')
        require(sum(r['scores'].values()) >= CONTRACT['score_total_minimum'][language], f'{candidate_id}/{language}: total below gate')
    require(selected[0]['independent_submission_ref'] != selected[1]['independent_submission_ref'], 'reviews cannot share one submission receipt')
    require(all(abs(selected[0]['scores'][a] - selected[1]['scores'][a]) < 2 for a in selected[0]['scores']), 'unresolved quality disagreement')


def screen_record(record, language, must_pass=True):
    queries = record.get('queries', [])
    require(len({q.get('query') for q in queries}) >= CONTRACT['query_minimum'], 'insufficient distinct search queries')
    require(set(CONTRACT['query_kinds'][language]) <= {q.get('kind') for q in queries}, 'missing query coverage')
    for q in queries:
        fields(q, ['query', 'executed_at', 'result_summary'], 'query record')
    if must_pass:
        require(record.get('status') == 'pass_public_precheck', 'final candidate has not passed independent screening')


def validate_search_plan(run, require_accepted=False):
    """Validate traceable fields; editorial merit still requires human/agent review."""
    plan = json.loads((run / 'search-plan.json').read_text())
    require(plan.get('no_new_names') is True, 'search plan must not contain new candidate names')
    fields(plan, ['directions', 'unknown_name_policy', 'pilot_plan'], 'search plan')
    directions = plan['directions']
    require(len({d.get('id') for d in directions}) == len(directions), 'duplicate plan direction id')
    expected = set(CONTRACT['planning']['macro_directions'])
    require(expected <= {d.get('macro_id') for d in directions}, 'search plan missing macro direction')
    baseline = run / 'inputs/A1/cases.json'
    if not baseline.exists():
        baseline = run / 'cases.json'
    cases = {c['id']: c for c in json.loads(baseline.read_text())['cases']}
    for d in directions:
        fields(d, ['id', 'macro_id', 'case_refs', 'transfer_mechanism', 'questions',
                   'queries', 'planned_sources', 'selection_criteria', 'rejection_criteria',
                   'history_risks', 'next_deliverable'], 'plan direction')
        require(d['macro_id'] in expected, 'invalid plan macro direction')
        require(len({x.get('case_id') for x in d['case_refs']}) >= 2, 'plan needs concrete cases')
        for c in d['case_refs']:
            fields(c, ['case_id', 'name', 'analysis_location', 'case_finding', 'evidence_boundary'], 'plan case')
            require(c['case_id'] in cases, 'unknown A1 case in search plan')
            require(c['name'] == cases[c['case_id']]['name'], 'plan A1 case name mismatch')
        require(all(d[k] for k in ['planned_sources', 'selection_criteria', 'rejection_criteria', 'history_risks', 'next_deliverable']), 'empty plan task fields')
        require(len(d['questions']) >= 2, 'plan needs concrete reading questions')
        require(d['queries'].get('zh') and d['queries'].get('en'), 'plan needs Chinese and English queries')
    if require_accepted:
        review = json.loads((run / 'plan-review.json').read_text())
        require(review.get('status') == 'accepted', 'search plan not accepted')
        reviewed = {x.get('direction_id') for x in review.get('direction_reviews', []) if x.get('status') == 'accepted'}
        require(reviewed == {d['id'] for d in directions}, 'plan direction review incomplete')
        reference(run, review['plan_ref'])
    return {d['id'] for d in directions}


def validate(run):
    run = Path(run)
    meta = json.loads((run / 'run.json').read_text())
    require(meta.get('protocol_version') in CONTRACT.get('supported_versions', [CONTRACT['version']]), 'new run must declare protocol_version from supported versions')
    require(meta['protocol_version'] == CONTRACT['version'] or run.name in CONTRACT.get('prior_protocol_runs', {}).get(meta['protocol_version'], []), 'new run cannot downgrade protocol version')
    require(meta.get('run_id') == run.name, 'run_id must match directory')
    fields(meta, ['date', 'coordinator_id', 'status'], 'run')
    require(meta['status'] in {'in_progress', 'incomplete', 'complete_with_candidates', 'complete_without_candidates'}, 'invalid run status')
    if meta['status'] in {'in_progress', 'incomplete'}:
        final = json.loads((run / 'final.json').read_text()) if (run / 'final.json').exists() else {}
        require(not final.get('candidates'), 'incomplete run cannot advertise final candidates')
        if meta['protocol_version'] == '1.1' and (run / 'search-plan.json').exists():
            validate_search_plan(run)
        return 'INCOMPLETE: no workflow compliance claimed'

    for filename in CONTRACT['required_files']:
        if meta['protocol_version'] == '1.0' and filename in {'search-plan.json', 'search-plan.md', 'plan-review.json'}:
            continue
        require((run / filename).is_file(), f'missing {filename}')
    data = {p.stem: json.loads(p.read_text()) for p in run.glob('*.json')}
    roles = meta.get('roles', {})
    require(set(roles) == set(CONTRACT['roles']), 'must execute all four roles')
    agent_ids = set()
    for role, execution in roles.items():
        fields(execution, ['agent_id', 'execution_ref', 'started_at', 'completed_at'], role)
        require(execution.get('status') == 'completed', f'{role} did not complete')
        require(datetime.fromisoformat(execution['started_at']) <= datetime.fromisoformat(execution['completed_at']), 'invalid role time range')
        agent_ids.add(execution['agent_id'])
    require(len(agent_ids) == 4 and meta['coordinator_id'] not in agent_ids, 'four agents must be distinct and separate from coordinator')

    mode = meta.get('research_mode', 'bootstrap')
    require(mode in CONTRACT['case_minimum'], 'invalid research mode')
    if mode == 'continuation':
        require(meta.get('baseline_refs'), 'continuation needs accepted case baseline')
        for ref in meta['baseline_refs']:
            reference(run, ref)
    cases = data['cases']['cases']
    require(len({c['id'] for c in cases}) == len(cases), 'duplicate case id')
    require(len(cases) >= CONTRACT['case_minimum'][mode], 'case research quota not met')
    case_counts = Counter(c.get('category') for c in cases)
    require(all(case_counts[k] >= CONTRACT['case_category_minimum'][mode] for k in CONTRACT['case_categories']), 'case market coverage missing')
    for c in cases:
        fields(c, ['id', 'name', 'word_origin_fact', 'naming_analysis', 'reading_scope', 'sources'], 'case')
        require(any(x.get('url') and x.get('access') == 'body' and x.get('supports') for x in c['sources']), 'case needs opened supporting body evidence')
    principles = data['cases']['principles']
    require(len(principles) >= CONTRACT['principle_minimum'], 'not enough transferable principles')
    for p in principles:
        fields(p, ['id', 'positive_example', 'counterexample', 'boundary'], 'principle')
    require(len(data['cases']['counterexamples']) >= CONTRACT['counterexample_minimum'], 'missing negative examples')

    plan_ids = validate_search_plan(run, require_accepted=True) if meta['protocol_version'] == '1.1' else None
    materials = data['materials']['materials']
    material_ids = {m['id'] for m in materials}
    require(len(material_ids) == len(materials), 'duplicate material id')
    require(len({m['family_id'] for m in materials}) >= CONTRACT['material_family_minimum'], 'independent material family quota missing')
    category_counts = Counter(m['category'] for m in materials)
    require(len(category_counts) >= CONTRACT['source_category_minimum'], 'source diversity quota missing')
    require(max(category_counts.values()) / len(materials) <= CONTRACT['source_category_max_share'], 'one source category dominates')
    require(sum(bool(m.get('is_classical')) for m in materials) / len(materials) <= CONTRACT['classical_max_share'], 'classical source quota exceeded')
    read_body = []
    for m in materials:
        if plan_ids is not None:
            fields(m, CONTRACT['planning']['material_lineage_fields'], 'material lineage')
            require(m['plan_direction_id'] in plan_ids, 'material plan direction missing')
            require(m['case_ids'] and set(m['case_ids']) <= {c['id'] for c in cases}, 'material case lineage broken')
        fields(m, ['id', 'family_id', 'category', 'reading_scope', 'reading_location', 'source_urls', 'fact'], 'material')
        if m['reading_scope'] in {'full_text', 'chapter', 'excerpt'}:
            read_body.append(m)
    require(len({m['book_id'] for m in read_body if m.get('source_type') == 'book' and m.get('book_id')}) >= CONTRACT['book_minimum'], 'book body reading quota missing')
    as_of = date.fromisoformat(meta['date'])
    news = [m for m in read_body if m.get('source_type') == 'news' and m.get('published_at') and 0 <= (as_of - date.fromisoformat(m['published_at'])).days <= CONTRACT['recent_news_days']]
    require(len(news) >= CONTRACT['recent_news_minimum'], 'recent news body reading quota missing')

    candidates = data['candidates']['candidates']
    by_id = {c['id']: c for c in candidates}
    require(len(by_id) == len(candidates), 'duplicate candidate id')
    require(len({c['family_id'] for c in candidates}) >= CONTRACT['candidate_family_target'], 'independent candidate family target not met')
    principle_ids = {p['id'] for p in principles}
    for c in candidates:
        if plan_ids is not None:
            fields(c, CONTRACT['planning']['candidate_lineage_fields'], 'candidate lineage')
        fields(c, ['id', 'name', 'family_id', 'material_ids', 'principle_ids', 'meaning', 'combination_reason', 'weakness', 'history_check'], 'candidate')
        require(set(c['material_ids']) <= material_ids and c['material_ids'], 'candidate material lineage broken')
        require(set(c['principle_ids']) <= principle_ids and c['principle_ids'], 'candidate principle lineage broken')
        fields(c['history_check'], ['status', 'reason'], 'history check')

    handoffs = data['handoffs']['handoffs']
    accepted = {}
    endpoints = {'H1': ('A1', 'A2'), 'H2': ('A2', 'coordinator'), 'H3': ('coordinator', 'A3'), 'H4': ('A3', 'A4'), 'H5': ('A4', 'A3'), 'H6': ('A3', 'coordinator'), 'H7': ('coordinator', 'user')}
    for h in handoffs:
        fields(h, ['id', 'status', 'from', 'to', 'timestamp', 'reason', 'input_refs', 'output_refs'], 'handoff')
        require(h['id'] in endpoints and (h['from'], h['to']) == endpoints[h['id']], 'invalid handoff endpoints')
        require(h['status'] in {'accepted', 'returned', 'zero_input'}, 'invalid handoff status')
        if h['id'] in accepted:
            require(datetime.fromisoformat(h['timestamp']) >= datetime.fromisoformat(accepted[h['id']]['timestamp']), 'handoff receipts out of order')
        for ref in h['input_refs'] + h['output_refs']:
            reference(run, ref)
        require(h['input_refs'] and h['output_refs'], 'handoff needs input and output artifacts')
        if h['status'] != 'returned':
            require(set(CONTRACT['handoff_output_files'][h['id']]) <= {Path(x['path']).name for x in h['output_refs']}, 'handoff missing role-specific deliverable')
            accepted[h['id']] = h
        else:
            accepted.pop(h['id'], None)
    require(set(accepted) == set(CONTRACT['handoffs']), 'missing accepted or zero-input stage receipt')
    times = [datetime.fromisoformat(accepted[k]['timestamp']) for k in CONTRACT['handoffs']]
    require(times == sorted(times), 'handoff order violated')
    require(all(accepted[k]['status'] == 'accepted' for k in ['H1', 'H2']), 'research stages cannot be skipped as zero-input')
    for h in accepted.values():
        require('candidate_ids' in h and set(h['candidate_ids']) <= set(by_id), 'handoff references unknown candidates')
        require(h['status'] != 'zero_input' or not h['candidate_ids'], 'zero-input receipt has candidate inputs')
        require(h['id'] == 'H1' or h['status'] != 'accepted' or h['candidate_ids'], 'empty stage needs explicit zero-input receipt')
    require(set(accepted['H2']['candidate_ids']) == set(by_id), 'H2 omitted generated candidates')

    cn_active = [x for x in data['screening']['chinese'] if x['status'] != 'not_screened_editorial']
    for x in cn_active:
        require(x.get('candidate_id') in by_id and x.get('name') == by_id[x['candidate_id']]['name'], 'Chinese screen name mismatch')
        review_pair(data['quality']['reviews'], x['candidate_id'], 'zh', x['name'])
        screen_record(x, 'zh', must_pass=False)
    cn_passed = {x['candidate_id'] for x in cn_active if x['status'] == 'pass_public_precheck'}
    en_entries = data['english']['entries']
    require(all(e.get('candidate_id') in cn_passed for e in en_entries), 'Agent4 received Chinese that did not pass screening')
    en_active = [x for x in data['screening']['english'] if x['status'] != 'not_screened_editorial']
    for x in en_active:
        require(any(e['candidate_id'] == x['candidate_id'] and e['name'] == x['name'] for e in en_entries), 'untraceable English screening')
        review_pair(data['quality']['reviews'], x['candidate_id'], 'en', x['name'])
        screen_record(x, 'en', must_pass=False)
    expected_inputs = {
        'H3': {x['candidate_id'] for x in cn_active},
        'H4': cn_passed,
        'H5': {x['candidate_id'] for x in en_active},
        'H6': {x['candidate_id'] for x in en_active if x['status'] == 'pass_public_precheck'},
    }
    for hid, ids in expected_inputs.items():
        require(set(accepted[hid]['candidate_ids']) == ids, f'{hid} input population mismatch')
    controls = data['screening'].get('positive_controls', [])
    require(len(controls) >= CONTRACT['positive_controls_minimum'], 'missing positive controls')
    require(set(CONTRACT['positive_control_types']) <= {c.get('entity_type') for c in controls if c.get('detected') is True and c.get('url')}, 'company/product controls must detect known use')
    finals = data['final']['candidates']
    require((meta['status'] == 'complete_with_candidates') == bool(finals), 'run status contradicts final count')
    final_ids = set()
    families = set()
    for f in finals:
        fields(f, ['id', 'family_id', 'chinese', 'english', 'source_ids'], 'final candidate')
        require(f['id'] in by_id and f['id'] not in final_ids, 'duplicate or unknown final candidate')
        c = by_id[f['id']]
        require(c['history_check']['status'] == 'new', 'historical or uncertain family counted as new')
        require(f['family_id'] == c['family_id'] and f['family_id'] not in families, 'same family counted twice')
        require(f['chinese'] == c['name'] and f['source_ids'] and set(f['source_ids']) <= material_ids, 'final source/name mismatch')
        final_ids.add(f['id'])
        families.add(f['family_id'])
        for language, name in [('zh', f['chinese']), ('en', f['english'])]:
            review_pair(data['quality']['reviews'], f['id'], language, name)
            matches = [x for x in data['screening']['chinese' if language == 'zh' else 'english'] if x.get('candidate_id') == f['id'] and x.get('name') == name]
            require(len(matches) == 1, 'missing independent name-specific screening')
            screen_record(matches[0], language)
            if language == 'zh':
                registry = matches[0].get('registry_checks', [])
                require({('CN', t) for t in ['company', 'trademark_9', 'trademark_42']} <= {(x.get('region'), x.get('type')) for x in registry}, 'mainland company/trademark attempts missing')
                require(any(x.get('region') != 'CN' and x.get('type') == 'company' for x in registry), 'international company attempt missing')
                for x in registry:
                    fields(x, ['region', 'type', 'status', 'url', 'attempted_at', 'detail'], 'registry check')
                    require(x['status'] in {'verified', 'unavailable'}, 'final registry query cannot silently be not_checked')
    require(set(accepted['H7']['candidate_ids']) == final_ids, 'H7 delivery differs from finals')

    rejections = data['rejections']['entries']
    for x in rejections:
        fields(x, ['candidate_id', 'name', 'language', 'stage', 'reason_code', 'reason'], 'rejection')
        require(x['reason_code'] in CONTRACT['rejection_codes'], 'unknown rejection reason code')
        if x['reason_code'] == 'EXACT_TECH_USE':
            require(x.get('evidence'), 'exact-use rejection needs named evidence')
            for e in x['evidence']:
                fields(e, ['entity_name', 'match_type', 'url', 'checked_at', 'access'], 'rejection evidence')
                require(e['access'] == 'body', 'exact-use rejection requires opened body evidence')
    rejected_keys = {(x['candidate_id'], x['language'], x['name']) for x in rejections}
    require(all((c['id'], 'zh', c['name']) in rejected_keys for c in candidates if c['id'] not in final_ids), 'missing per-name Chinese exclusion reason')
    selected_en = {(f['id'], f['english']) for f in finals}
    require(all((e['candidate_id'], 'en', e['name']) in rejected_keys for e in data['english']['entries'] if (e['candidate_id'], e['name']) not in selected_en), 'missing per-name English exclusion reason')
    rework_attempts = set()
    for x in data.get('rework', {}).get('entries', []):
        require(x.get('language') in {'zh', 'en'} and type(x.get('attempt')) is int and 1 <= x['attempt'] <= CONTRACT['rework_limit'][x['language']], 'rework limit exceeded')
        fields(x, ['candidate_id', 'reason', 'responsible_role', 'before_refs', 'after_refs'], 'rework')
        require(x['candidate_id'] in by_id, 'rework references unknown candidate')
        family = by_id[x['candidate_id']]['family_id'] if x['language'] == 'zh' else x['candidate_id']
        key = (family, x['language'], x['attempt'])
        require(key not in rework_attempts, 'duplicate rework attempt for family')
        rework_attempts.add(key)
        require(x['before_refs'] and x['after_refs'], 'rework needs before and after artifacts')
        for ref in x['before_refs'] + x['after_refs']:
            reference(run, ref)
    return f'FORMAL CHECKS PASSED: {len(finals)} pairs; real execution/source/editorial audit still required'
