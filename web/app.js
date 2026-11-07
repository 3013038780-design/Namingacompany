/* Read-only research browser. The repository is the source of truth. */
const FEED='https://raw.githubusercontent.com/3013038780-design/Namingacompany/codex/naming-research-pilot/research/catalog/website.json';
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const url=v=>/^https?:\/\//.test(String(v))?esc(v):'#';
const external=(href,label,cls='text-link')=>`<a class="${cls}" href="${url(href)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
const dateTime=v=>new Date(v).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
let data=null,world='all',status='discussion_candidate',query='',lastRemote=false;
const labels={discussion_candidate:'讨论备选',research_reserve:'研究储备',withdrawn:'已撤回'};
function badge(v){return `<span class="badge ${v==='withdrawn'?'gray':v==='research_reserve'?'warn':''}">${labels[v]||esc(v)}</span>`}
function worldName(id){return data.worlds.find(w=>w.id===id)?.title||id}
function render(){
 if(!data)return;
 $('#stat-discussion').textContent=data.counts.discussion_candidates;
 $('#stat-reserve').textContent=data.counts.research_reserves;
 $('#stat-pending').textContent=data.pending_evidence.length;
 $('#nav-count').textContent=data.counts.discussion_candidates;
 $('#registry-note').textContent=data.notice;
 $('#updated-at').textContent='研究数据更新于 '+dateTime(data.generated_at)+'（北京时间）';
 $('#record-link').href=data.links.research;$('#repo-link').href=data.links.catalog;
 $('#sync-status').textContent=lastRemote?'● 已连接最新研究数据':'○ 暂用保存的研究快照';
 const latest=data.events[0];
 $('#latest-card').innerHTML=latest?`<div class="latest-date">最近一次完成<b>${esc(dateTime(latest.at))}</b></div><div class="latest-body"><h3>${latest.drafts} 个中文提案 · ${latest.retained} 组新增备选${latest.pending?' · '+latest.pending+' 项待核实':''}</h3><p>${latest.retained?'新名字已收入总库，来源和双语查重随名字保存。':'本次没有新增通过的双语名字；具体去留和证据已记录。'}</p></div><a class="latest-arrow" href="#updates" aria-label="查看本次更新">↗</a>`:'';
 $('#worlds').innerHTML=[{id:'all',title:'全部方向'},...data.worlds].map(w=>{const count=data.entries.filter(e=>e.status===status&&(w.id==='all'||e.primary_world===w.id)).length;return `<button data-world="${w.id}" class="${world===w.id?'active':''}" aria-pressed="${world===w.id}">${esc(w.title)}<small>${count}</small></button>`}).join('');
 renderCards();renderUpdates();renderResearch();route();
}
function renderCards(){
 if(!data)return;
 const entries=[...data.entries].sort((a,b)=>(b.record_date||'').localeCompare(a.record_date||'')).filter(e=>e.status===status&&(world==='all'||e.primary_world===world)&&(!query||[e.chinese,e.english,e.meaning,e.brief,e.source?.title,e.crossing].join(' ').toLowerCase().includes(query.toLowerCase())));
 $('#visible-count').textContent=`${entries.length} 个名字`;
 $('#cards').innerHTML=entries.length?entries.map(e=>`<button class="name-card" data-id="${e.id}" aria-label="查看${esc(e.chinese)}的出处与查重"><div class="card-top"><span>${esc(worldName(e.primary_world))}</span>${badge(e.status)}</div><h3>${esc(e.chinese)}</h3><div class="en" lang="en">${esc(e.english)}</div><p class="card-brief">${esc(e.brief||e.meaning)}</p><div class="card-bottom"><span>初筛 ${esc((e.screened_dates||[]).at(-1)||'日期见记录')}</span><span aria-hidden="true">↗</span></div></button>`).join(''):'<div class="empty">暂时没有符合条件的名字。试试其他方向或关键词。</div>';
 document.querySelectorAll('#status-filters button').forEach(b=>{b.classList.toggle('active',b.dataset.status===status);b.setAttribute('aria-pressed',b.dataset.status===status)});
}
function renderUpdates(){
 const days=[...new Set(data.events.map(e=>e.date))];
 $('#timeline').innerHTML=days.map(day=>{const events=data.events.filter(e=>e.date===day),n=events.reduce((a,e)=>a+e.retained,0);return `<section class="day"><div class="day-head"><h3>${esc(day.replaceAll('-','.'))}</h3><span>完成 ${events.length} 次研究更新 · ${n} 组新增通过</span></div>${events.map(e=>`<article class="event"><time datetime="${esc(e.at)}">${esc(new Date(e.at).toLocaleTimeString('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false}))}</time><div><h4>${esc(e.title)}</h4><div class="numbers">${e.materials} 项资料 · ${e.drafts} 个中文提案 · ${e.retained} 组新增${e.pending?' · '+e.pending+' 项待核实':''}</div><p>${esc(e.reason)}</p>${external(e.record_url,'查看本次完整记录')}</div></article>`).join('')}</section>`}).join('');
}
function renderResearch(){
 $('#pending-list').innerHTML=data.pending_evidence.map(p=>`<article class="pending-card"><h3>${esc(p.chinese)} <span class="en">/ ${esc(p.english)}</span>　<span class="badge warn">待核实 · 非完整备选</span></h3><p>${esc(p.detail)}</p>${external('https://github.com/3013038780-design/Namingacompany/blob/codex/naming-research-pilot/'+p.record,'查看未核实线索及查询记录')}</article>`).join('');
 const admitted=new Set(data.entries.filter(e=>e.status==='discussion_candidate').map(e=>e.chinese));
 $('#research-list').innerHTML=[...data.research].reverse().filter(e=>!admitted.has(e.chinese)).map(e=>`<article class="research-row"><div><h3>${esc(e.chinese)}</h3><span class="badge ${e.status.includes('待核实')?'warn':'gray'}">${esc(e.status)}</span></div><div><p>${esc(e.reason)}</p>${e.english_attempts?.length?`<p class="small-note">英文版本：${e.english_attempts.map(esc).join(' / ')}（同一家族，不算新增名字）</p>`:''}${external(e.record_url,'查看原始提案')}</div></article>`).join('');
}
function route(){
 const view=['library','updates','research'].includes(location.hash.slice(1))?location.hash.slice(1):'library';
 for(const v of ['library','updates','research'])$('#'+v+'-view').hidden=v!==view;
 document.querySelectorAll('[data-view]').forEach(a=>a.classList.toggle('active',a.dataset.view===view));
 const head={library:['THE NAME LIBRARY','名字，和它背后的世界。','从真实出处出发，寻找一个自然、好记、值得长久使用的称呼。'],updates:['THE RESEARCH JOURNAL','每次更新，都在这里。','新增、未保留和仍待核实的结果，按日期留下清楚的记录。'],research:['WORK IN PROGRESS','为什么留下，为什么放下。','资料真实只是起点；品牌气质、独立查重与证据完整性同样重要。']}[view];
 $('#page-kicker').textContent=head[0];$('#page-title').textContent=head[1];$('#page-subtitle').textContent=head[2];
}
function section(title,body){return `<section class="detail-section"><h4>${esc(title)}</h4>${body}</section>`}
function queryBlock(title,s,summary){
 const rows=s?.queries||[],reason=summary||s?.reason||'详见原始研究记录。';
 return `<p><b>${esc(title)}</b>　${esc(reason)}</p>${rows.length?`<details><summary>展开 ${rows.length} 条实际查询</summary>${rows.map(q=>{if(typeof q==='string')return `<div class="query"><code>${esc(q)}</code></div>`;return `<div class="query"><code>${esc(q.query||q.q||'')}</code><p>${esc(q.summary||q.result_summary||q.finding||'')} ${esc(q.executed_on||q.date||'')}</p></div>`}).join('')}</details>`:''}`;
}
function showDetail(id){
 const e=data.entries.find(x=>x.id===id);if(!e)return;
 $('#detail-category').textContent=worldName(e.primary_world)+' / '+e.id;
 const source=e.source||{};
 $('#detail-content').innerHTML=`<h2>${esc(e.chinese)}</h2><div class="en" lang="en">${esc(e.english)}</div><div class="detail-status">${badge(e.status)}　查重日期：${esc(e.screened_dates.join(' / '))}</div><p class="detail-intro">${esc(e.meaning||e.brief)}</p>`+
 section('真实出处',`<p class="source-title">${external(source.url,source.title||'查看来源','source-title')}</p><p>${esc(e.fact)}</p><p class="small-note">实际阅读范围：${esc(source.read_scope||source.reading_location||'原始记录中披露')}</p>`)+
 section('两个世界怎样相连',`<p>${esc(e.crossing)}</p>${e.layers?.length?`<ul>${e.layers.map(l=>`<li>${esc(l)}</li>`).join('')}</ul>`:''}`)+
 section('英文为什么这样配',`<p>${esc(e.english_formation)}</p><p>${esc(e.bilingual_relation)}</p><p class="small-note">建议读音：${esc(e.suggested_pronunciation)}</p>`)+
 section('需要一起考虑的短板',`<p>${esc(e.chinese_shortcoming)}</p><p>${esc(e.english_shortcoming)}</p>${e.source_boundary?`<p>${esc(e.source_boundary)}</p>`:''}`)+
 section('中英文独立使用筛查',queryBlock('中文',e.screening.zh,e.cn_screen_summary)+queryBlock('英文',e.screening.en,e.en_screen_summary)+`${e.review_note?`<p>后续复核：${esc(e.review_note)}</p>`:''}<p class="small-note">${esc(e.registration_note)}</p>${external(e.record_url,'查看完整查询、访问范围与登记限制')}`)+
 (e.status==='withdrawn'?section('撤回记录',`<p>${esc(e.review_note||e.revision_history?.at(-1)?.reason||'新证据出现后已撤回。')}</p>`):'');
 $('#detail').showModal();
}
$('#worlds').addEventListener('click',e=>{const b=e.target.closest('[data-world]');if(!b)return;world=b.dataset.world;render()});
$('#status-filters').addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(!b)return;status=b.dataset.status;world='all';render()});
$('#search').addEventListener('input',e=>{query=e.target.value.trim();renderCards()});
$('#cards').addEventListener('click',e=>{const card=e.target.closest('[data-id]');if(card)showDetail(card.dataset.id)});
$('#close-detail').addEventListener('click',()=>$('#detail').close());
$('#detail').addEventListener('click',e=>{if(e.target===$('#detail')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
window.addEventListener('hashchange',()=>{route();window.scrollTo(0,0)});
async function refresh(){
 try{const response=await fetch(FEED+'?v='+Math.floor(Date.now()/60000),{cache:'no-store'});if(!response.ok)throw Error(response.status);const next=await response.json();if(next.schema_version!==1||!Array.isArray(next.entries))throw Error('schema');data=next;lastRemote=true;render()}
 catch(error){lastRemote=false;if(data)render();else $('#sync-status').textContent='最新数据暂时不可读，正在加载保存快照…'}
}
async function init(){
 try{const response=await fetch('data.json');if(response.ok){data=await response.json();render()}}catch{}
 await refresh();
 if(!data)$('#cards').innerHTML='<div class="load-error">数据暂时无法载入。请稍后刷新，或打开页脚的研究仓库查看。</div>';
}
init();setInterval(refresh,60000);
