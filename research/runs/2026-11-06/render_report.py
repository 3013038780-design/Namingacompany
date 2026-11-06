import html
import json
from pathlib import Path

ROOT = Path(__file__).parent

def read(name, default=None):
    p = ROOT / name
    return json.loads(p.read_text()) if p.exists() else default

def esc(x):
    return html.escape(str(x))

def links(urls):
    return ' · '.join(f'<a href="{esc(u)}">来源 {i + 1}</a>' for i, u in enumerate(dict.fromkeys(urls)))

def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + cell + '</td>' for cell in row) + '</tr>' for row in rows) + '</tbody></table></div>'

cases = read('cases.json', {})
materials = read('materials.json', {})
candidates = read('candidates.json', {})
screening = read('screening.json', {})
editorial = read('editorial.json', {})
final = read('final.json', {})
notes = {r['id']: r for r in editorial.get('rows', [])}
screens = {r['id']: r for r in screening.get('candidates', [])}
body = '<p class="eyebrow">NAMING LAB · 2026.11.06 · 最小循环</p><h1>名字如何从研究走到候选</h1>'
body += '<p class="lead">中文为主。每个创意家族只计一次，历史名字不计新增。此次只试跑，不创建每日自动化。</p>'
body += '<p>' + esc(final.get('summary', '研究结果整理中')) + '</p>'
body += '<h2>本轮留下的名字</h2>'
for r in final.get('pairs', []):
    body += '<article><h3>' + esc(r['chinese']) + ' <span>/ ' + esc(r['english']) + '</span></h3>'
    for label, key in [('读音', 'pronunciation'), ('来源与创作', 'origin'), ('组合关系', 'relation'), ('品牌寓意', 'meaning'), ('取舍', 'weakness'), ('初筛结果', 'screening')]:
        body += '<p><b>' + label + '</b>　' + esc(r.get(key, '')) + '</p>'
    body += '<p>' + links(r.get('source_urls', [])) + '</p></article>'
for r in final.get('reserves', []):
    body += '<p><b>中文储备：' + esc(r['name']) + '</b>　' + esc(r['reason']) + '</p>'
body += '<h2>案例研究：12 个样本</h2><p>品牌成功不是名字单独造成的。以下区分可核实事实与命名解读。</p>'
body += table(['品牌', '可核实事实', '命名分析', '来源'], [[esc(c['name']), esc(c['verified_or_bounded_fact']), esc(c['naming_analysis_not_founder_attribution']), links(c['sources'])] for c in cases.get('cases', [])])
body += '<h2>提炼出的原则</h2><ol>' + ''.join('<li>' + esc(s) + '</li>' for s in cases.get('principles', [])) + '</ol>'
body += '<h2>素材阅读：12 张卡</h2><p>' + esc(read('source_review.json', {}).get('book_reading_statement', '')) + '</p>'
body += table(['素材', '实际读到的内容', '命名关系', '阅读范围与来源'], [[esc(m['title']), esc(m['fact']), esc(m['naming_relation']), esc(m['reading_scope']) + '<br>' + links([m['source_url']] + ([m['book_source_url']] if m.get('book_source_url') else []))] for m in materials.get('materials', [])])
body += '<p>星尘炉的背景经复核已由黑洞吸积盘改为恒星元素合成。原始解释及修正保存在 source_review.json，不以原页面证明新背景。</p>'
body += '<h2>全部草案与去留</h2><p>24 个字面草案保守归并为 12 个素材／意象家族。同一家族不能重复计新增。</p>'
rows = []
for c in candidates.get('candidates', []):
    n, s = notes.get(c['id'], {}), screens.get(c['id'], {})
    rows.append([esc(c['id'] + ' · ' + c['name']), esc(n.get('family_id', '')), esc(c['meaning']), esc(n.get('reason', '')), esc(s.get('finding', '未进入占用检索')), links(s.get('evidence_urls', []))])
body += table(['草案', '家族', '释义', '编辑判断', '公开使用筛查', '证据'], rows)
body += '<h2>审查范围</h2><p>通过仅表示本轮未检出明确同名科技／AI品牌，不表示全球工商或商标可注册。国内官方工商与商标入口本轮返回403；英国登记入口可访问，逐名查询结果以英文筛查文件为准。近似名与完全同名分别记录。</p>'
body += '<p>已用 Confluence 与 Foldra 做阳性对照，确认现有 AI 与软件产品会被流程否决。</p>'
body += '<h2>完整研究记录</h2><p>' + ' · '.join(f'<a href="{p.name}">{esc(p.name)}</a>' for p in sorted(ROOT.glob('*.json'))) + '</p>'
style = 'body{max-width:1100px;margin:48px auto;padding:0 24px;font:16px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#26312f;background:#faf9f6}h1{font-size:36px;line-height:1.3}h2{margin-top:54px;font-size:24px}h3{font-size:26px;margin:0 0 20px}h3 span{font:26px Georgia,serif;color:#64716b}.eyebrow{letter-spacing:.15em;font-size:12px;color:#687a72}.lead{font-size:19px}article{background:white;border:1px solid #dedfd8;padding:28px;margin:22px 0;border-radius:10px}article p{margin:10px 0}a{color:#27745c}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.7}td,th{text-align:left;padding:13px;vertical-align:top;border-bottom:1px solid #dedfd8;min-width:90px}th{background:#eef0e9}.scroll{overflow-x:auto}li{margin:10px 0}@media(max-width:600px){body{margin:24px auto}h1{font-size:28px}article{padding:18px}}'
(ROOT / 'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>命名研究最小循环 · 2026-11-06</title><style>' + style + '</style><body>' + body + '</body></html>')
