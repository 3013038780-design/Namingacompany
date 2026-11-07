"""Publish a compact, read-only website feed from reviewed repository records."""
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'codex/naming-research-pilot'
BASE = 'https://github.com/3013038780-design/Namingacompany/blob/' + BRANCH + '/'
FEED_URL = 'https://raw.githubusercontent.com/3013038780-design/Namingacompany/' + BRANCH + '/research/catalog/website.json'


def read(path):
    return json.loads((ROOT / path).read_text())


def link(path):
    return BASE + quote(str(path), safe='/')


def reader_text(value):
    """Keep evidence meaning, with workflow shorthand expanded for readers."""
    result = str(value or '')
    for old, new in [
        ('不能英文R3', '后续只补充证据，不再更换英文'),
        ('不再R3', '不继续更换英文'), ('不R3', '不继续更换英文'),
        ('A4真实零输入、同A3真实零英文回查均已执行；', ''),
        ('原A3', '独立查重'), ('同A3', '同一独立审查'),
        ('原A4', '英文匹配'), ('主控', '品牌审阅'),
        ('官方app bundle', '官网公开发布的内容'),
        ('品牌审阅独立下载同SHA确认', '来源内容已独立复核'),
        ('原文403', '原文页面目前无法访问'),
    ]:
        result = result.replace(old, new)
    return result


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
    snapshots = {}
    for file in (ROOT / 'research/runs').glob('*/continuations/*/decisions-through-*.json'):
        value = json.loads(file.read_text())
        key = Path(*file.relative_to(ROOT).parts[:3])
        if value.get('updated_at', '') >= snapshots.get(key, ({}, None))[0].get('updated_at', ''):
            snapshots[key] = (value, file.relative_to(ROOT))
    snapshots[run] = (read(queue['latest_frozen_decision_snapshot']), Path(queue['latest_frozen_decision_snapshot']))
    research = []
    for history_run, (snapshot, snapshot_path) in sorted(snapshots.items()):
        proposals, attempts = {}, {}
        for file in sorted((ROOT / history_run).glob('A2-candidates-*.json')):
            for row in json.loads(file.read_text()).get('candidates', []):
                proposals[row['id']] = {**row, 'record_url': link(file.relative_to(ROOT))}
        for pattern in ('A4-batch*.json', 'A4-candidates-*.json'):
            for file in sorted((ROOT / history_run).glob(pattern)):
                for row in json.loads(file.read_text()).get('candidates', []):
                    cid = row.get('chinese_id')
                    if cid:
                        attempts.setdefault(cid, {})[row['id']] = row.get('english', '')
        for item in snapshot['items']:
            cid = item['chinese_id']
            proposal = proposals.get(cid, {})
            research.append({**item, 'run': str(history_run), 'reason': reader_text(item['reason']),
                             'source': proposal.get('sources', []), 'meaning': proposal.get('meaning', ''),
                             'crossing': proposal.get('crossing', ''), 'shortcoming': proposal.get('shortcoming', ''),
                             'record_url': proposal.get('record_url', link(snapshot_path)),
                             'english_attempts': list(attempts.get(cid, {}).values())})

    events = []
    for file in (ROOT / 'research/runs').glob('*/continuations/*/result.json'):
        value = json.loads(file.read_text())
        stamp = value.get('completed_at')
        if not stamp:
            continue
        stamp = datetime.fromisoformat(stamp.replace('Z', '+00:00')).astimezone(ZoneInfo('Asia/Shanghai')).isoformat()
        new_names = value.get('new_retained_families', 0)
        events.append({'id': str(file.relative_to(ROOT)), 'at': stamp, 'date': stamp[:10],
                       'title': '研究更新', 'retained': new_names,
                       'drafts': value.get('new_chinese_drafts', 0),
                       'materials': value.get('new_materials', 0),
                       'pending': value.get('evidence_holds', 0),
                       'reason': reader_text(value.get('reason', '')), 'record_url': link(file.relative_to(ROOT))})
    progress_path = Path('research/runs/2026-11-07-continuous-001/progress.json')
    progress = read(progress_path)
    stamp = progress.get('updated_at')
    if stamp:
        events.append({'id': 'main-segment', 'at': stamp, 'date': stamp[:10],
                       'title': '活桥、作数进入讨论备选', 'retained': progress['current_bilingual_retained'],
                       'drafts': progress['literal_chinese_drafts'], 'materials': progress['materials'],
                       'pending': 0, 'reason': '保留活桥 / Antspan、作数 / Factborne；余量补核后撤回。两个旧储备转入讨论，另列、不算新家族。更早的讨论备选已汇入名字库。',
                       'record_url': link(progress_path.parent / 'README.md')})
    events.sort(key=lambda x: x['at'], reverse=True)
    payload = {'schema_version': 1, 'generated_at': datetime.now().astimezone().isoformat(),
               'feed_url': FEED_URL, 'counts': catalog['counts'], 'worlds': catalog['worlds'],
               'entries': entries, 'research': research, 'events': events,
               'pending_evidence': [{**e, 'detail': reader_text(e['detail'])} for e in queue.get('pending_evidence', [])],
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
