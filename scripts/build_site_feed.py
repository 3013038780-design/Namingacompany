"""Publish a compact, read-only website feed from reviewed repository records."""
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'codex/naming-research-pilot'
BASE = 'https://github.com/3013038780-design/Namingacompany/blob/' + BRANCH + '/'
FEED_URL = 'https://raw.githubusercontent.com/3013038780-design/Namingacompany/' + BRANCH + '/research/catalog/website.json'


def read(path):
    return json.loads((ROOT / path).read_text())


def link(path):
    return BASE + quote(str(path), safe='/')


def screen(value):
    if not isinstance(value, dict):
        return {'queries': [], 'evidence': []}
    return {
        'decision': value.get('decision', value.get('status', '')),
        'reason': value.get('reason', value.get('summary', '')),
        'queries': [({k: q[k] for k in ('query', 'q', 'executed_on', 'date', 'summary', 'result_summary', 'finding') if k in q}
                     if isinstance(q, dict) else q)
                    for q in value.get('query_logs', value.get('queries', [])) if isinstance(q, (dict, str))],
        'evidence': value.get('evidence', []),
        'registration': value.get('registration', {}),
    }


def build():
    catalog = read('research/catalog/catalog.json')
    queue = read('research/continuation-queue.json')
    entries = []
    for original in catalog['entries']:
        entry = dict(original)
        entry['record_url'] = link(entry['origin_record'])
        doc = read(entry['origin_record'])
        rows = doc if isinstance(doc, list) else doc.get('discussion_pairs', doc.get('items', []))
        source = next((x for x in rows if x.get('chinese_id', x.get('id')) == entry['origin_chinese_id']), {})
        entry['screening'] = {'zh': screen(source.get('chinese_screen')), 'en': screen(source.get('english_screen'))}
        entry['record_date'] = source.get('terminal_review', {}).get('reviewed_at') or (entry.get('screened_dates') or [''])[0]
        entries.append(entry)

    run = Path(queue['active_run'])
    proposals = {}
    for file in sorted((ROOT / run).glob('A2-candidates-*.json')):
        for row in json.loads(file.read_text()).get('candidates', []):
            proposals[row['id']] = {**row, 'record_url': link(file.relative_to(ROOT))}
    attempts = {}
    for pattern in ('A4-batch*.json', 'A4-candidates-*.json'):
        for file in sorted((ROOT / run).glob(pattern)):
            for row in json.loads(file.read_text()).get('candidates', []):
                cid = row.get('chinese_id')
                if cid:
                    attempts.setdefault(cid, {})[row['id']] = row.get('english', '')
    snapshot = read(queue['latest_frozen_decision_snapshot'])
    research = []
    for item in snapshot['items']:
        cid = item['chinese_id']
        proposal = proposals.get(cid, {})
        research.append({**item, 'source': proposal.get('sources', []),
                         'meaning': proposal.get('meaning', ''), 'crossing': proposal.get('crossing', ''),
                         'shortcoming': proposal.get('shortcoming', ''),
                         'record_url': proposal.get('record_url', link(queue['latest_frozen_decision_snapshot'])),
                         'english_attempts': list(attempts.get(cid, {}).values())})

    events = []
    for file in (ROOT / run / 'continuations').glob('*/result.json'):
        value = json.loads(file.read_text())
        stamp = value.get('completed_at')
        if not stamp:
            continue
        new_names = value.get('new_retained_families', 0)
        events.append({'id': file.parent.name, 'at': stamp, 'date': stamp[:10],
                       'title': '研究更新', 'retained': new_names,
                       'drafts': value.get('new_chinese_drafts', 0),
                       'materials': value.get('new_materials', 0),
                       'pending': value.get('evidence_holds', 0),
                       'reason': value.get('reason', ''), 'record_url': link(file.relative_to(ROOT))})
    progress_path = run / 'progress.json'
    progress = read(progress_path)
    stamp = progress.get('updated_at')
    if stamp:
        events.append({'id': 'main-segment', 'at': stamp, 'date': stamp[:10],
                       'title': '活桥、作数进入讨论备选', 'retained': progress['current_bilingual_retained'],
                       'drafts': progress['literal_chinese_drafts'], 'materials': progress['materials'],
                       'pending': 0, 'reason': '保留活桥 / Antspan、作数 / Factborne；余量补核后撤回。两个旧储备转入讨论，另列、不算新家族。更早的讨论备选已汇入名字库。',
                       'record_url': link(run / 'README.md')})
    events.sort(key=lambda x: x['at'], reverse=True)
    payload = {'schema_version': 1, 'generated_at': datetime.now().astimezone().isoformat(),
               'feed_url': FEED_URL, 'counts': catalog['counts'], 'worlds': catalog['worlds'],
               'entries': entries, 'research': research, 'events': events,
               'pending_evidence': queue.get('pending_evidence', []),
               'scheduler': {'status': queue['scheduler']['status'], 'cadence': queue['scheduler']['cadence']},
               'links': {'catalog': link('research/catalog/README.md'),
                         'research': link(run / 'README.md'), 'pr': 'https://github.com/3013038780-design/Namingacompany/pull/4'},
               'notice': '公开使用初筛是带日期的研究快照；未完成正式公司核名或第9/42类商标核验。'}
    out = ROOT / 'research/catalog/website.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'website_feed': str(out), 'entries': len(entries), 'events': len(events), 'research': len(research)}, ensure_ascii=False))
    return payload


if __name__ == '__main__':
    build()
