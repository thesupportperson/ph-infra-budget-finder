let data=[];
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat('en-PH',{style:'currency',currency:'PHP',maximumFractionDigits:0}).format(n||0);
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const values=key=>[...new Set(data.map(x=>x[key]).filter(Boolean))].sort();
const addOptions=(id,key)=>values(key).forEach(v=>$(id).add(new Option(String(v).replaceAll('_',' '),v)));
const levelName=value=>String(value||'budget_line').replaceAll('_',' ');
const sourceLink=x=>x.source_url?`${esc(x.source_url)}${x.source_pdf_page?`#page=${encodeURIComponent(x.source_pdf_page)}`:''}`:'';
function filtered(){
  const q=$('q').value.trim().toLowerCase(),min=+$('min').value||0,max=+$('max').value||Infinity;
  return data.filter(x=>{
    const hay=Object.values(x).join(' ').toLowerCase();
    return (!q||hay.includes(q))&&(!$('year').value||x.fiscal_year==$('year').value)&&(!$('region').value||x.region==$('region').value)&&(!$('type').value||x.project_type==$('type').value)&&(!$('level').value||x.row_level==$('level').value)&&($('include-summary').checked||Number(x.is_leaf)!==0)&&(x.amount||0)>=min&&(x.amount||0)<=max;
  });
}
function render(){
  const rows=filtered(),total=rows.reduce((s,x)=>s+(x.amount||0),0),large=Math.max(0,...rows.map(x=>x.amount||0));
  $('total').textContent=money(total); $('count').textContent=rows.length.toLocaleString(); $('largest').textContent=money(large);
  $('source-linked').textContent=rows.filter(x=>x.extraction_confidence==='source_linked').length.toLocaleString();
  $('result-note').textContent=`${rows.length.toLocaleString()} of ${data.length.toLocaleString()} records shown`;
  $('empty').hidden=!!rows.length;
  $('rows').innerHTML=rows.map(x=>`<tr><td><details><summary>${esc(x.project_title)}</summary><p>${esc(x.review_reason||'No review note recorded.')}<br>${sourceLink(x)?`<a href="${sourceLink(x)}" target="_blank" rel="noopener">Open official source page</a>`:'No source URL recorded'}${x.source_page?` · Printed budget page ${esc(x.source_page)}`:''}</p></details></td><td>${money(x.amount)}</td><td>${esc(levelName(x.row_level))}</td><td class="location">${esc([x.region,x.province,x.city_municipality].filter(Boolean).join(' · ')||'Location not recorded')}</td><td>${esc(x.implementing_office||'—')}</td><td>${esc((x.project_type||'unknown').replaceAll('_',' '))}</td><td>${x.review_label?`<span class="tag">${esc(x.review_label)}</span>`:'—'}</td><td>${sourceLink(x)?`<a href="${sourceLink(x)}" target="_blank" rel="noopener">DBM PDF${x.source_page?` p. ${esc(x.source_page)}`:''}</a>`:'—'}</td></tr>`).join('');
}
function download(){
  const rows=filtered(),keys=['id','fiscal_year','budget_stage','agency','region','province','city_municipality','implementing_office','project_title','project_type','row_level','parent_row_id','is_leaf','amount','review_label','review_reason','extraction_confidence','extraction_note','source_name','source_url','source_page','source_pdf_page'];
  const csv=[keys.join(','),...rows.map(r=>keys.map(k=>`"${String(r[k]??'').replaceAll('"','""')}"`).join(','))].join('\n');
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'})); a.download='ph-infra-budget-filtered.csv'; a.click(); URL.revokeObjectURL(a.href);
}
fetch('data/projects.json').then(r=>{if(!r.ok)throw Error();return r.json()}).then(json=>{
  data=json; addOptions('year','fiscal_year'); addOptions('region','region'); addOptions('type','project_type'); addOptions('level','row_level');
  $('generated').textContent=`${data.length.toLocaleString()} OFFICIAL FY 2026 DPWH LINES · STATIC DATASET`; render();
}).catch(()=>{$('result-note').textContent='Could not load the local dataset. Serve this folder with a local web server.';$('empty').hidden=false;$('empty').textContent='Dataset unavailable. Check site/data/projects.json.'});
['q','year','region','type','level','min','max','include-summary'].forEach(id=>$(id).addEventListener(id==='q'?'input':'change',render));
$('search').onclick=render; $('clear').onclick=()=>{document.querySelectorAll('input:not([type=checkbox]),select').forEach(x=>x.value='');$('include-summary').checked=false;render()}; $('download-filtered').onclick=download;


fetch('data/factuality_report.json').then(r=>r.json()).then(report=>{
  const target=$('factuality-status');
  if(target) target.textContent=report.verdict==='VERIFIED' ? `Independent source check: VERIFIED · ${Number(report.records_checked).toLocaleString()} rows` : 'Independent source check: see report';
}).catch(()=>{const target=$('factuality-status');if(target)target.textContent='Independent source check unavailable';});
