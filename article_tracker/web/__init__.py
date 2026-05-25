from __future__ import annotations


def get_html() -> str:
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Article Tracker 配置面板</title>
<style>
:root{--bg:#f8fafc;--card:#fff;--text:#0f172a;--muted:#667085;--border:#e5e7eb;--acc:#2563eb;--acc2:#7c3aed;--danger:#ef4444;--success:#10b981}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;background:var(--bg);color:var(--text);line-height:1.6}
.container{max-width:960px;margin:0 auto;padding:20px}
h1{font-size:24px;margin-bottom:4px}
.subtitle{color:var(--muted);font-size:14px;margin-bottom:20px}
.tabs{display:flex;gap:4px;margin-bottom:20px;flex-wrap:wrap}
.tab{padding:8px 16px;border-radius:8px 8px 0 0;cursor:pointer;font-size:14px;font-weight:600;border:1px solid var(--border);border-bottom:none;background:#fff;color:var(--muted);transition:.2s}
.tab.active{background:var(--card);color:var(--acc);border-color:var(--acc)}
.tab:hover{color:var(--acc)}
.panel{display:none;background:var(--card);border:1px solid var(--border);border-radius:0 8px 8px 8px;padding:24px}
.panel.active{display:block}
.field{margin-bottom:16px}
.field label{display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:var(--text)}
.field .hint{font-size:12px;color:var(--muted);margin-bottom:4px}
.field input[type=text],.field input[type=number],.field select,.field textarea{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;background:#fff}
.field textarea{min-height:80px;resize:vertical}
.field input[type=checkbox]{width:18px;height:18px;accent-color:var(--acc);margin-right:8px;vertical-align:middle}
.row{display:flex;gap:12px;flex-wrap:wrap}
.row .field{flex:1;min-width:200px}
.tags{display:flex;flex-wrap:wrap;gap:6px;padding:8px 0}
.tag{background:#ede9fe;color:var(--acc2);padding:3px 10px;border-radius:999px;font-size:13px;cursor:pointer;transition:.2s}
.tag:hover{background:#ddd6fe}
.tag .del{margin-left:6px;opacity:.6;font-weight:700}
.tag .del:hover{opacity:1;color:var(--danger)}
.add-tag{display:flex;gap:6px;margin-top:4px}
.add-tag input{flex:1;padding:6px 10px;border:1px solid var(--border);border-radius:8px;font-size:13px}
.add-tag button{padding:6px 14px;background:var(--acc);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:13px}
.add-tag button:hover{background:#1d4ed8}
.btn{padding:10px 24px;border:none;border-radius:10px;cursor:pointer;font-size:14px;font-weight:600;transition:.2s}
.btn-primary{background:var(--acc);color:#fff}
.btn-primary:hover{background:#1d4ed8}
.btn-success{background:var(--success);color:#fff}
.btn-success:hover{background:#059669}
.btn-danger{background:var(--danger);color:#fff}
.btn-danger:hover{background:#dc2626}
.btn-outline{background:#fff;color:var(--text);border:1px solid var(--border)}
.btn-outline:hover{border-color:var(--acc);color:var(--acc)}
.actions{display:flex;gap:10px;margin-top:20px;padding-top:16px;border-top:1px solid var(--border)}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:10px;color:#fff;font-size:14px;font-weight:600;z-index:999;opacity:0;transition:.3s;pointer-events:none}
.toast.show{opacity:1}
.toast.success{background:var(--success)}
.toast.error{background:var(--danger)}
.journal-list{display:flex;flex-wrap:wrap;gap:6px}
.journal-item{background:#f0f9ff;color:#0369a1;padding:3px 10px;border-radius:999px;font-size:13px}
.switch{position:relative;display:inline-block;width:44px;height:24px}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#cbd5e1;border-radius:24px;transition:.3s}
.slider:before{position:absolute;content:"";height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s}
.switch input:checked+.slider{background:var(--acc)}
.switch input:checked+.slider:before{transform:translateX(20px)}
.status-bar{display:flex;gap:12px;align-items:center;margin-bottom:16px;font-size:13px;color:var(--muted)}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}
.status-dot.green{background:var(--success)}
.status-dot.red{background:var(--danger)}
</style>
</head>
<body>
<div class="container">
<h1>Article Tracker 配置面板</h1>
<p class="subtitle">修改配置后点击「保存配置」，无需手动编辑 YAML</p>

<div class="tabs">
<div class="tab active" onclick="switchTab('source')">数据源</div>
<div class="tab" onclick="switchTab('screening')">筛选策略</div>
<div class="tab" onclick="switchTab('output')">输出通道</div>
<div class="tab" onclick="switchTab('advanced')">高级设置</div>
</div>

<!-- 数据源面板 -->
<div id="panel-source" class="panel active">
<h3 style="margin-bottom:16px">arXiv 预印本</h3>
<div class="field">
<label class="hint">启用 arXiv 源</label>
<label class="switch"><input type="checkbox" id="arxiv-enabled" onchange="markDirty()"><span class="slider"></span></label>
</div>
<div class="field">
<label>arXiv 分类</label>
<div class="hint">如 cs.CV, cs.AI, cs.LG, cs.CL</div>
<div id="arxiv-categories" class="tags"></div>
<div class="add-tag"><input id="add-cat-input" placeholder="添加分类，如 cs.RO"><button onclick="addTag('arxiv-categories','add-cat-input')">添加</button></div>
</div>
<div class="field">
<label>搜索关键词</label>
<div id="arxiv-keywords" class="tags"></div>
<div class="add-tag"><input id="add-kw-input" placeholder="添加关键词"><button onclick="addTag('arxiv-keywords','add-kw-input')">添加</button></div>
</div>
<div class="field">
<label>排除关键词</label>
<div id="arxiv-exclude" class="tags"></div>
<div class="add-tag"><input id="add-exc-input" placeholder="添加排除词"><button onclick="addTag('arxiv-exclude','add-exc-input')">添加</button></div>
</div>
<div class="row">
<div class="field"><label>逻辑关系</label><select id="arxiv-logic" onchange="markDirty()"><option value="AND">AND（分类 AND 关键词）</option><option value="OR">OR（分类 OR 关键词）</option></select></div>
<div class="field"><label>最大返回数</label><input type="number" id="arxiv-max-results" value="50" onchange="markDirty()"></div>
</div>

<h3 style="margin:24px 0 16px">顶刊论文（Semantic Scholar 主搜索）</h3>
<div class="field">
<label class="hint">启用顶刊源</label>
<label class="switch"><input type="checkbox" id="tj-enabled" onchange="markDirty()"><span class="slider"></span></label>
</div>
<div class="row">
<div class="field"><label>回溯天数</label><input type="number" id="tj-since-days" value="7" onchange="markDirty()"><div class="hint">1=仅当天，7=近一周</div></div>
<div class="field"><label>每刊最大返回数</label><input type="number" id="tj-max-per-journal" value="50" onchange="markDirty()"></div>
</div>
<div class="field">
<label>追踪期刊</label>
<div id="tj-watchlist" class="journal-list"></div>
<div class="add-tag" style="margin-top:8px"><input id="add-journal-input" placeholder="添加期刊名"><button onclick="addJournal()">添加</button></div>
</div>
</div>

<!-- 筛选策略面板 -->
<div id="panel-screening" class="panel">
<h3 style="margin-bottom:16px">四层筛选</h3>
<div class="field">
<label>Core 关键词（核心领域，高度相关）</label>
<div id="screen-core" class="tags"></div>
<div class="add-tag"><input id="add-core-input" placeholder="添加核心关键词"><button onclick="addTag('screen-core','add-core-input')">添加</button></div>
</div>
<div class="field">
<label>Proxy 关键词（方法相关，领域不同）</label>
<div id="screen-proxy" class="tags"></div>
<div class="add-tag"><input id="add-proxy-input" placeholder="添加代理关键词"><button onclick="addTag('screen-proxy','add-proxy-input')">添加</button></div>
</div>
<div class="field">
<label>Eco 关键词（领域相关，方法不同）</label>
<div id="screen-eco" class="tags"></div>
<div class="add-tag"><input id="add-eco-input" placeholder="添加生态关键词"><button onclick="addTag('screen-eco','add-eco-input')">添加</button></div>
</div>
<div class="field">
<label>排除关键词</label>
<div id="screen-exclusion" class="tags"></div>
<div class="add-tag"><input id="add-scr-exc-input" placeholder="添加排除词"><button onclick="addTag('screen-exclusion','add-scr-exc-input')">添加</button></div>
</div>
<div class="field">
<label>必追踪期刊（无论关键词匹配与否）</label>
<div id="screen-must-journals" class="tags"></div>
<div class="add-tag"><input id="add-mustj-input" placeholder="添加期刊名"><button onclick="addTag('screen-must-journals','add-mustj-input')">添加</button></div>
</div>
<div class="field">
<label>输出层级</label>
<div class="hint">选择要输出哪些层级（noise 不输出）</div>
<div id="output-tiers" style="display:flex;gap:12px;flex-wrap:wrap">
<label><input type="checkbox" id="tier-core" checked onchange="markDirty()"> core</label>
<label><input type="checkbox" id="tier-proxy" checked onchange="markDirty()"> proxy</label>
<label><input type="checkbox" id="tier-eco" checked onchange="markDirty()"> eco</label>
</div>
</div>
</div>

<!-- 输出通道面板 -->
<div id="panel-output" class="panel">
<h3 style="margin-bottom:16px">九通道输出</h3>
<div class="row">
<div class="field"><label>JSON</label><label class="switch"><input type="checkbox" id="out-json" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>Markdown</label><label class="switch"><input type="checkbox" id="out-md" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>HTML 交互表</label><label class="switch"><input type="checkbox" id="out-html" onchange="markDirty()"><span class="slider"></span></label></div>
</div>
<div class="row">
<div class="field"><label>PDF</label><label class="switch"><input type="checkbox" id="out-pdf" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>Excel</label><label class="switch"><input type="checkbox" id="out-excel" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>Obsidian</label><label class="switch"><input type="checkbox" id="out-obsidian" onchange="markDirty()"><span class="slider"></span></label></div>
</div>
<div class="row">
<div class="field"><label>Zotero</label><label class="switch"><input type="checkbox" id="out-zotero" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>邮件推送</label><label class="switch"><input type="checkbox" id="out-email" onchange="markDirty()"><span class="slider"></span></label></div>
<div class="field"><label>GitHub Pages</label><label class="switch"><input type="checkbox" id="out-ghpages" onchange="markDirty()"><span class="slider"></span></label></div>
</div>

<div id="email-config" style="margin-top:16px;display:none;border-top:1px solid var(--border);padding-top:16px">
<h3 style="margin-bottom:12px">邮件配置</h3>
<div class="row">
<div class="field"><label>SMTP 服务器</label><input type="text" id="smtp-server" onchange="markDirty()"></div>
<div class="field"><label>SMTP 端口</label><input type="number" id="smtp-port" value="465" onchange="markDirty()"></div>
</div>
<div class="row">
<div class="field"><label>发件人</label><input type="text" id="email-sender" onchange="markDirty()"></div>
<div class="field"><label>收件人（逗号分隔）</label><input type="text" id="email-to" onchange="markDirty()"></div>
</div>
</div>

<div id="llm-config" style="margin-top:16px;border-top:1px solid var(--border);padding-top:16px">
<h3 style="margin-bottom:12px">LLM 双语摘要</h3>
<div class="field"><label>启用 LLM</label><label class="switch"><input type="checkbox" id="llm-enabled" onchange="markDirty();toggleLlm()"><span class="slider"></span></label></div>
<div id="llm-detail" style="display:none">
<div class="row">
<div class="field"><label>API 地址</label><input type="text" id="llm-base-url" onchange="markDirty()"></div>
<div class="field"><label>模型名称</label><input type="text" id="llm-model" onchange="markDirty()"></div>
</div>
</div>
</div>
</div>

<!-- 高级设置面板 -->
<div id="panel-advanced" class="panel">
<h3 style="margin-bottom:16px">去重策略</h3>
<div class="row">
<div class="field"><label>标题模糊匹配阈值</label><input type="number" id="dedup-threshold" value="0.85" step="0.05" min="0" max="1" onchange="markDirty()"><div class="hint">0~1，越大越严格</div></div>
<div class="field"><label>优先保留源</label><select id="dedup-prefer" onchange="markDirty()"><option value="top_journal">top_journal（顶刊优先）</option><option value="arxiv">arxiv（预印本优先）</option></select></div>
</div>
<h3 style="margin:24px 0 16px">新鲜度与回退</h3>
<div class="row">
<div class="field"><label>回溯天数</label><input type="number" id="freshness-since" value="7" onchange="markDirty()"><div class="hint">1=仅当天，7=近一周</div></div>
<div class="field"><label>论文最大年龄（天）</label><input type="number" id="freshness-max-age" value="365" onchange="markDirty()"></div>
</div>
<div class="row">
<div class="field"><label>无新增时回退</label><label class="switch"><input type="checkbox" id="freshness-fallback" onchange="markDirty()"><span class="slider"></span></label><div class="hint">当无新论文时，回退展示最近的 Top N</div></div>
<div class="field"><label>回退展示数</label><input type="number" id="freshness-fallback-n" value="10" onchange="markDirty()"></div>
</div>
</div>

<div class="actions">
<button class="btn btn-primary" onclick="saveConfig()">保存配置</button>
<button class="btn btn-success" onclick="triggerTrack()">运行追踪</button>
<button class="btn btn-outline" onclick="location.reload()">重置</button>
</div>
</div>

<div id="toast" class="toast"></div>

<script>
let config={}, dirty=false;
function switchTab(id){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('panel-'+id).classList.add('active');
}
function markDirty(){dirty=true}
function toast(msg,type='success'){
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast '+type+' show';
  setTimeout(()=>t.classList.remove('show'),3000);
}
function renderTags(containerId,items){
  const c=document.getElementById(containerId);c.innerHTML='';
  items.forEach(item=>{
    const s=document.createElement('span');s.className='tag';
    s.innerHTML=item+'<span class="del" onclick="removeTag(\''+containerId+'\',\''+item.replace(/'/g,"\\'")+'\')">&times;</span>';
    c.appendChild(s);
  });
}
function getTags(containerId){
  return [...document.getElementById(containerId).querySelectorAll('.tag')].map(t=>t.textContent.replace('×','').trim());
}
function removeTag(containerId,item){
  const items=getTags(containerId).filter(i=>i!==item);
  renderTags(containerId,items);markDirty();
}
function addTag(containerId,inputId){
  const inp=document.getElementById(inputId);const v=inp.value.trim();
  if(!v)return;const items=getTags(containerId);
  if(!items.includes(v)){items.push(v);renderTags(containerId,items);markDirty();}
  inp.value='';
}
function addJournal(){
  const inp=document.getElementById('add-journal-input');const v=inp.value.trim();
  if(!v)return;
  const c=document.getElementById('tj-watchlist');
  const s=document.createElement('span');s.className='journal-item';
  s.innerHTML=v+'<span class="del" style="margin-left:6px;cursor:pointer;opacity:.6" onclick="this.parentElement.remove();markDirty()">&times;</span>';
  c.appendChild(s);inp.value='';markDirty();
}
function toggleLlm(){document.getElementById('llm-detail').style.display=document.getElementById('llm-enabled').checked?'block':'none'}
function toggleEmail(){document.getElementById('email-config').style.display=document.getElementById('out-email').checked?'block':'none'}

async function loadConfig(){
  try{
    const r=await fetch('/api/v1/config');config=await r.json();
    // arxiv
    document.getElementById('arxiv-enabled').checked=config.arxiv?.enabled??true;
    renderTags('arxiv-categories',config.arxiv?.categories||[]);
    renderTags('arxiv-keywords',config.arxiv?.keywords||[]);
    renderTags('arxiv-exclude',config.arxiv?.exclude_keywords||[]);
    document.getElementById('arxiv-logic').value=config.arxiv?.logic||'AND';
    document.getElementById('arxiv-max-results').value=config.arxiv?.max_results||50;
    // top journal
    document.getElementById('tj-enabled').checked=config.top_journal?.enabled??true;
    document.getElementById('tj-since-days').value=config.top_journal?.since_days||7;
    document.getElementById('tj-max-per-journal').value=config.top_journal?.max_per_journal||50;
    const wl=document.getElementById('tj-watchlist');wl.innerHTML='';
    (config.top_journal?.watchlist||[]).forEach(j=>{
      const s=document.createElement('span');s.className='journal-item';
      s.innerHTML=(j.name||j)+'<span class="del" style="margin-left:6px;cursor:pointer;opacity:.6" onclick="this.parentElement.remove();markDirty()">&times;</span>';
      wl.appendChild(s);
    });
    // screening
    renderTags('screen-core',config.screening?.core_keywords||[]);
    renderTags('screen-proxy',config.screening?.proxy_keywords||[]);
    renderTags('screen-eco',config.screening?.eco_keywords||[]);
    renderTags('screen-exclusion',config.screening?.exclusion_keywords||[]);
    renderTags('screen-must-journals',config.screening?.must_track_journals||[]);
    const tiers=config.screening?.output_tiers||['core','proxy','eco'];
    document.getElementById('tier-core').checked=tiers.includes('core');
    document.getElementById('tier-proxy').checked=tiers.includes('proxy');
    document.getElementById('tier-eco').checked=tiers.includes('eco');
    // output
    document.getElementById('out-json').checked=config.output?.json_enabled??true;
    document.getElementById('out-md').checked=config.output?.md_enabled??true;
    document.getElementById('out-html').checked=config.output?.html_table_enabled??true;
    document.getElementById('out-pdf').checked=config.output?.pdf_enabled??false;
    document.getElementById('out-excel').checked=config.output?.excel_enabled??false;
    document.getElementById('out-obsidian').checked=config.output?.obsidian_enabled??false;
    document.getElementById('out-zotero').checked=config.output?.zotero_enabled??false;
    document.getElementById('out-email').checked=config.output?.email?.enabled??false;
    document.getElementById('out-ghpages').checked=config.output?.ghpages?.enabled??false;
    toggleEmail();
    document.getElementById('smtp-server').value=config.output?.email?.smtp_server||'';
    document.getElementById('smtp-port').value=config.output?.email?.smtp_port||465;
    document.getElementById('email-sender').value=config.output?.email?.sender||'';
    document.getElementById('email-to').value=(config.output?.email?.to||[]).join(', ');
    // llm
    document.getElementById('llm-enabled').checked=config.llm?.enabled??false;
    document.getElementById('llm-base-url').value=config.llm?.base_url||'';
    document.getElementById('llm-model').value=config.llm?.model||'';
    toggleLlm();
    // advanced
    document.getElementById('dedup-threshold').value=config.dedup?.title_threshold||0.85;
    document.getElementById('dedup-prefer').value=config.dedup?.prefer_source||'top_journal';
    document.getElementById('freshness-since').value=config.freshness?.since_days||7;
    document.getElementById('freshness-max-age').value=config.freshness?.max_age_days||365;
    document.getElementById('freshness-fallback').checked=config.freshness?.fallback_when_empty??false;
    document.getElementById('freshness-fallback-n').value=config.freshness?.fallback_top_n||10;
  }catch(e){toast('加载配置失败: '+e.message,'error')}
}

async function saveConfig(){
  const wl=[...document.getElementById('tj-watchlist').querySelectorAll('.journal-item')].map(e=>{
    const text=e.textContent.replace('×','').trim();return {name:text};
  });
  const tiers=[];
  if(document.getElementById('tier-core').checked)tiers.push('core');
  if(document.getElementById('tier-proxy').checked)tiers.push('proxy');
  if(document.getElementById('tier-eco').checked)tiers.push('eco');
  const data={
    arxiv:{
      enabled:document.getElementById('arxiv-enabled').checked,
      categories:getTags('arxiv-categories'),
      keywords:getTags('arxiv-keywords'),
      exclude_keywords:getTags('arxiv-exclude'),
      logic:document.getElementById('arxiv-logic').value,
      max_results:parseInt(document.getElementById('arxiv-max-results').value),
      sort_by:config.arxiv?.sort_by||'submittedDate',
      sort_order:config.arxiv?.sort_order||'descending',
    },
    top_journal:{
      enabled:document.getElementById('tj-enabled').checked,
      since_days:parseInt(document.getElementById('tj-since-days').value),
      max_per_journal:parseInt(document.getElementById('tj-max-per-journal').value),
      watchlist:wl,
    },
    dedup:{
      seen_path:config.dedup?.seen_path||'.state/seen.json',
      title_threshold:parseFloat(document.getElementById('dedup-threshold').value),
      prefer_source:document.getElementById('dedup-prefer').value,
    },
    screening:{
      output_tiers:tiers,
      core_keywords:getTags('screen-core'),
      proxy_keywords:getTags('screen-proxy'),
      eco_keywords:getTags('screen-eco'),
      exclusion_keywords:getTags('screen-exclusion'),
      must_track_journals:getTags('screen-must-journals'),
    },
    llm:{
      enabled:document.getElementById('llm-enabled').checked,
      base_url:document.getElementById('llm-base-url').value,
      model:document.getElementById('llm-model').value,
      api_key_env:config.llm?.api_key_env||'DS_API_KEY',
      api_key:'',system_prompt_zh:'',system_prompt_en:'',
      timeout:config.llm?.timeout||60,
    },
    output:{
      dir:config.output?.dir||'outputs',
      json_enabled:document.getElementById('out-json').checked,
      md_enabled:document.getElementById('out-md').checked,
      html_table_enabled:document.getElementById('out-html').checked,
      pdf_enabled:document.getElementById('out-pdf').checked,
      excel_enabled:document.getElementById('out-excel').checked,
      obsidian_enabled:document.getElementById('out-obsidian').checked,
      zotero_enabled:document.getElementById('out-zotero').checked,
      email:{
        enabled:document.getElementById('out-email').checked,
        sender:document.getElementById('email-sender').value,
        to:document.getElementById('email-to').value.split(',').map(s=>s.trim()).filter(Boolean),
        smtp_server:document.getElementById('smtp-server').value,
        smtp_port:parseInt(document.getElementById('smtp-port').value),
        smtp_user:config.output?.email?.smtp_user||'',
        smtp_pass_env:config.output?.email?.smtp_pass_env||'SMTP_PASS',
        smtp_pass:'',tls_mode:'auto',subject_prefix:'Paper Tracker',
      },
      ghpages:{
        enabled:document.getElementById('out-ghpages').checked,
        output_dir:config.output?.ghpages?.output_dir||'docs',
        keep_runs:config.output?.ghpages?.keep_runs||30,
        accent:'#2563eb',theme_mode:'auto',
      },
    },
    freshness:{
      since_days:parseInt(document.getElementById('freshness-since').value),
      max_age_days:parseInt(document.getElementById('freshness-max-age').value),
      fallback_when_empty:document.getElementById('freshness-fallback').checked,
      fallback_top_n:parseInt(document.getElementById('freshness-fallback-n').value),
    },
    s2:config.s2||{api_key_env:'S2_API_KEY',api_key:'',base_url:'https://api.semanticscholar.org/graph/v1'},
    openalex:config.openalex||{email_env:'OPENALEX_EMAIL',email:'',base_url:'https://api.openalex.org'},
    source_filter:'all',dry_run:false,verbose:false,
  };
  try{
    const r=await fetch('/api/v1/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const res=await r.json();
    if(res.status==='saved'){toast('配置已保存');dirty=false;config=data;}
    else toast('保存失败: '+(res.error||'未知错误'),'error');
  }catch(e){toast('保存失败: '+e.message,'error')}
}

async function triggerTrack(){
  try{
    const r=await fetch('/api/v1/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({config_path:'config.yaml',source:'all'})});
    const res=await r.json();
    toast('追踪已触发 (task: '+res.task_id+')');
  }catch(e){toast('触发失败: '+e.message,'error')}
}

document.getElementById('out-email').addEventListener('change',toggleEmail);
loadConfig();
</script>
</body>
</html>
"""
