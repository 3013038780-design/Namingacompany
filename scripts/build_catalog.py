"""Rebuild the cumulative, classified reading entry from explicit accepted sources."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'research/catalog'
def load(p):return json.loads(p.read_text())
def esc(s):return str(s or '').replace('|','／').replace('\n',' ')
def link(p):return '../../'+str(p)
def dates(screen):return sorted({q.get('executed_on') or str(q.get('executed_at',''))[:10] for q in screen.get('query_logs',screen.get('queries',[]))}-{''})
manifest=load(DEST/'sources.json');tax=load(DEST/'classification.json');entries=[];seen=set();families=set()
ledger_path=DEST/'ids.json'
ledger=load(ledger_path) if ledger_path.exists() else ({e['family_id']:e['id'] for e in load(DEST/'catalog.json')['entries']} if (DEST/'catalog.json').exists() else {})
assert len(set(ledger.values()))==len(ledger), 'stable ID reused'
next_id=max((int(v[1:]) for v in ledger.values()),default=0)+1
for source in manifest['sources']:
 p=ROOT/source['path'];assert p.exists(),p
 for row in load(p)[source['array']]:
  reserve='chinese_draft' in row
  c=row['chinese_draft'] if reserve else row
  e=row['english_draft'] if reserve else row
  name=row['chinese'];en=row['english'];assert name not in seen,('duplicate Chinese',name);seen.add(name)
  family=c['family_id'];assert family not in families,('duplicate family',family);families.add(family)
  if family not in ledger:
   ledger[family]=f'N{next_id:04d}';next_id+=1
  cls=tax['names'][name];assert cls['primary'] in {w['id'] for w in tax['worlds']}
  cn=row['chinese_use_record'] if reserve else row['chinese_screen'];eng=row['english_use_record'] if reserve else row['english_screen']
  assert cn.get('decision',cn.get('status')) in {'public_use_screen_pass','pass_public_precheck'}
  assert eng.get('decision',eng.get('status')) in {'public_use_screen_pass','pass_public_precheck'}
  entries.append({'id':ledger[family],'chinese':name,'english':en,'family_id':family,'status':source['status'],'primary_world':cls['primary'],'tags':cls['tags'],'classification_reason':cls['reason'],'brief':cls.get('brief',c.get('meaning')),'source':c['source'],'fact':c.get('fact'),'meaning':c.get('meaning'),'crossing':c.get('crossing'),'layers':c.get('layers',[]),'chinese_shortcoming':c.get('shortcoming',c.get('weakness')),'english_formation':e.get('formation',e.get('english_formation')),'bilingual_relation':e.get('bilingual_relation'),'english_shortcoming':e.get('shortcoming') if reserve else e.get('english_shortcoming',e.get('english_weakness')),'source_boundary':c.get('lost',c.get('scientific_boundary')),'suggested_pronunciation':e.get('suggested_pronunciation'),'cn_screen_summary':cn.get('reason'),'en_screen_summary':eng.get('reason'),'screened_dates':sorted(set(dates(cn)+dates(eng))),'origin_record':source['path'],'origin_chinese_id':c.get('id',c.get('chinese_id')),'origin_english_id':e.get('id',e.get('english_id')),'chinese_registration_record':cn.get('registration',cn.get('registry_checks')),'english_registration_record':eng.get('registration',eng.get('registry_checks')),'registration_status':'not_officially_cleared','registration_note':'原始记录逐入口披露；公开使用初筛不是企业核名或9/42类商标可注册结论。'})
assert len({e['id'] for e in entries})==len(entries)
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
counts={'discussion_candidates':sum(e['status']=='discussion_candidate' for e in entries),'research_reserves':sum(e['status']=='research_reserve' for e in entries),'total_unique_families':len(entries)}
(DEST/'catalog.json').write_text(json.dumps({'schema_version':1,'purpose':'持续分类总库；无每日配额。不同英文版本不增加家族数。','counts':counts,'worlds':tax['worlds'],'entries':entries},ensure_ascii=False,indent=2)+'\n')
lines=['# 科技公司命名总库','','**一个持续更新的入口，按方向选名字，不按日期翻报告。** 当前收录'+str(counts['discussion_candidates'])+'组公开使用初筛讨论备选、'+str(counts['research_reserves'])+'组研究储备；合计'+str(counts['total_unique_families'])+'个独立家族。没有每日配额或累计数量终点。','','[逐名完整解释与查重入口](names.md) · [结构化总库](catalog.json) · [正在研究什么](../continuation-queue.json) · [105组品牌案例分类](../runs/2026-11-06-agent1-baseline105/README.md)','','“讨论备选”经过本轮来源、质量与中英文公开使用筛查；“研究储备”沿用原轮次状态，不自动升级推荐。官方登记状态均按原记录披露，未声称可注册。查重是有日期的快照，不是永久保证。新研究、待核实和已否决名字不混入备选总数。','','## 按来源世界浏览','','分类继承105组研究的六个大方向；一个名字只设一个主分类，跨领域关系用标签表示。造词、音译、组合属于构词方式，不另当素材世界。','']
for world in tax['worlds']:
 group=[e for e in entries if e['primary_world']==world['id']]
 lines +=[f'## {world["id"]} {world["title"]}', '',world['description'], '']
 if not group:lines+=['暂缺合格条目，持续寻找；不为填分类造名字。',''];continue
 lines+=['| 中文 | English | 故事的内核 | 状态 |','| --- | --- | --- | --- |']
 for e in group:
  status='讨论备选' if e['status']=='discussion_candidate' else '研究储备'
  lines.append(f'| [**{e["chinese"]}**](names.md#{e["id"].lower()}) | {e["english"]} | {esc(e["brief"])} | {status} |')
 lines.append('')
lines+=['## 还在研究或已经淘汰的记录','','- [当前研究001](../runs/2026-11-07-continuous-001/README.md)：未完成的研究不会提前算备选。','- [上一轮逐名去留](../runs/2026-11-07-continuation/rejections.md)：包括真实撞名、近似避让、质量和家族淘汰，分别写清原因。','- [完整历史轮次](../runs/)：旧名、返工及不同版本保留，不覆盖原始证据。','','## 更新方式','','每有合格新增，将来源文件登记到sources.json，并写清classification.json主分类和交叉理由，再运行 `python3 scripts/build_catalog.py`。只显式汇入终审通过或清楚标为储备的条目；不能扫描所有草案自动推荐。稳定编号按来源登记顺序分配，既有来源顺序与条目顺序不改；撤回保留原编号及原因，不删除后重编号。后续如有同一家族新英文，以同一总库ID记录版本，不新增一条。','','总库更新不改原始轮次快照；新的审美或查重结论追加带日期的修订记录。自动任务接续同一队列和现有PR，不因跨日或达到20结束。']
(DEST/'README.md').write_text('\n'.join(lines).rstrip()+'\n')
detail=['# 名字、出处与双语查重','','[返回分类总库](README.md)。以下是可讨论名字与明确标记的研究储备，来源事实和品牌分析分开。登记未清空，切勿把公开搜索未见同名理解为法律可用。','']
for e in entries:
 status='讨论备选' if e['status']=='discussion_candidate' else '研究储备'
 detail +=[f'<a id="{e["id"].lower()}"></a>','',f'## {e["chinese"]} · {e["english"]}', '',f'**{status}** · {e["primary_world"]} · 查重日期：'+ '、'.join(e['screened_dates']), '',f'- **真实出处**：[{e["source"]["title"]}]({e["source"]["url"]})。实读范围：{e["source"].get("read_scope", "见原记录")}',f'- **来源事实**：{e["fact"]}',f'- **为什么找到这里 / 交叉点**：{e["crossing"]}',f'- **寓意**：{e["meaning"]}',f'- **多层含义**：'+ '；'.join(e['layers']),f'- **中文短板**：{e["chinese_shortcoming"]}',f'- **英文构词**：{e["english_formation"]}',f'- **中英文关系**：{e["bilingual_relation"]}',f'- **英文短板**：{e["english_shortcoming"]}',f'- **中文使用检索**：{e["cn_screen_summary"]}',f'- **英文使用检索**：{e["en_screen_summary"]}',f'- **分类理由与交叉标签**：{e["classification_reason"]} '+ ' / '.join(e['tags']),f'- **全部查询、分数、访问范围及登记状态**：[原始逐名记录]({link(e["origin_record"])})；原中文ID {e["origin_chinese_id"]}，英文ID {e["origin_english_id"]}。','']
 if e['source_boundary']:detail +=[f'事实边界：{e["source_boundary"]}','']
(DEST/'names.md').write_text('\n'.join(detail).rstrip()+'\n')
print(json.dumps(counts,ensure_ascii=False))
