'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const percent = n => `${(100*n).toFixed(1)}%`;
let cohort = [], predictions = [], metadata;

async function api(path, body) {
  const response = await fetch(path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(e=>`${e.loc.slice(1).join('.')}: ${e.msg}`).join('; ') : data.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data;
}
function showError(error) { $('error').hidden=false; $('error').textContent=error.message; }
function clearError() { $('error').hidden=true; }
function view(name) {
  document.querySelectorAll('.view').forEach(s=>s.hidden=s.id!==name);
  document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
  $('breadcrumb').textContent = {queue:'ORDER QUEUE',predict:'CHECK AN ORDER',evidence:'MODEL EVIDENCE'}[name];
  clearError();
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>view(b.dataset.open)));

async function updateQueue(nextCohort=cohort) {
  clearError(); $('refresh').disabled=true;
  try {
    const budget=Number($('budget').value);
    if (!Number.isInteger(budget)||budget<1||budget>500) throw new Error('Choose a whole-number review capacity from 1 to 500.');
    const result=await api('/predict/batch',{orders:nextCohort,investigation_budget:budget});
    cohort=nextCohort; predictions=result.orders;
    const byId=new Map(cohort.map(o=>[o.order_id,o]));
    $('order-count').textContent=cohort.length;
    $('selected-count').textContent=result.selected;
    $('max-risk').textContent=percent(predictions[0].delay_probability);
    $('orders').innerHTML=predictions.map(p=>{
      const o=byId.get(p.order_id);
      const days=Math.round((Date.parse(o.promised_date)-Date.parse(o.approved_at.slice(0,10)))/86400000);
      return `<tr><td class="rank">${String(p.rank).padStart(2,'0')}</td><td><strong>${escapeHTML(p.order_id)}</strong><span class="sub">${escapeHTML(o.primary_category.replaceAll('_',' '))}</span></td><td>${escapeHTML(o.seller_state)} <span style="color:#9aaba2">→</span> ${escapeHTML(o.customer_state)}</td><td>${days} days<span class="sub">${escapeHTML(o.promised_date)}</span></td><td><div class="risk-cell"><strong>${percent(p.delay_probability)}</strong><span class="risk-bar"><i style="width:${100*p.delay_probability}%"></i></span></div><span class="sub">${escapeHTML(p.risk_band)}${p.warnings.length?' · check inputs':''}</span></td><td><span class="badge ${p.selected_for_review?'':'wait'}">${p.selected_for_review?'Review':'Outside capacity'}</span></td></tr>`;
    }).join('');
    $('queue-description').textContent=`${result.selected} of ${cohort.length} orders selected. Capacity applies to this batch.`;
  } catch(error) { showError(error); } finally { $('refresh').disabled=false; }
}
$('refresh').addEventListener('click',()=>updateQueue());
$('reset-demo').addEventListener('click',async()=>{try{const d=await api('/demo-orders');await updateQueue(d.orders);document.querySelector('.notice').innerHTML='<strong>Demo queue</strong><span>These are invented example orders scored by the trained model. They are not live orders or measured outcomes.</span>';}catch(e){showError(e);}});
$('upload').addEventListener('change',async event=>{
  try {
    const file=event.target.files[0]; if(!file)return;
    if(file.size>1_000_000)throw new Error('Use a JSON file smaller than 1 MB.');
    const data=JSON.parse(await file.text());
    const orders=Array.isArray(data)?data:data.orders;
    if(!Array.isArray(orders)||!orders.length||orders.length>500)throw new Error('The file must contain an orders array with 1 to 500 orders. See examples/demo_batch.json.');
    await updateQueue(orders);
    if(cohort===orders)document.querySelector('.notice').innerHTML='<strong>Imported batch</strong><span>These predictions are unverified for current operations. Review input warnings and the historical model scope.</span>';
  }catch(e){showError(e);}finally{event.target.value='';}
});
$('download').addEventListener('click',()=>{
  const url=URL.createObjectURL(new Blob([JSON.stringify({model_version:metadata.model_version,orders:predictions},null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='delaylens_review_queue.json';link.click();URL.revokeObjectURL(url);
});
$('predict-form').addEventListener('submit',async event=>{
  event.preventDefault();clearError();const button=event.target.querySelector('button[type="submit"]');button.disabled=true;
  try{
    const order=Object.fromEntries(new FormData(event.target));
    for(const k of ['item_count','total_price_brl','freight_brl'])order[k]=Number(order[k]);
    for(const k of ['total_weight_g','total_volume_cm3'])order[k]=order[k]===''?null:Number(order[k]);
    const p=await api('/predict',order);
    $('result').innerHTML=`<div class="probability">${percent(p.delay_probability)}</div><h2>${escapeHTML(p.risk_band[0].toUpperCase()+p.risk_band.slice(1))} relative risk</h2><p>Estimated chance of arriving after the promised calendar date, within the model's historical delivered-order scope.</p><ul>${p.warnings.map(w=>`<li>${escapeHTML(w)}</li>`).join('')}</ul><p style="font-size:9px;overflow-wrap:anywhere">${escapeHTML(p.model_version)}</p>`;
  }catch(e){showError(e);}finally{button.disabled=false;}
});
function renderEvidence(report) {
  const t=report.test, c=t.capacity_50, ci=report.bootstrap_95_percent;
  $('lift').textContent=`${c.lift_over_random.toFixed(2)}×`;
  $('evidence-content').innerHTML=`<div class="stats"><article><span>Legacy cohort orders</span><strong>${t.orders.toLocaleString()}</strong><small>${percent(t.late_rate)} were delivered late</small></article><article><span>Average precision</span><strong>${t.average_precision.toFixed(3)}</strong><small>Baseline: ${report.test_constant_prior.average_precision.toFixed(3)}</small></article><article><span>Precision at 50/day</span><strong>${percent(c.precision)}</strong><small>95% day-bootstrap interval: ${percent(ci.precision_at_50_per_day[0])}–${percent(ci.precision_at_50_per_day[1])}</small></article><article class="accent"><span>Late orders found</span><strong>${c.late_found} / ${t.late_orders}</strong><small>${percent(c.recall)} recall; ${c.selected.toLocaleString()} orders reviewed</small></article></div><div class="panel"><div class="panel-title"><div><h2>Superseded selection on March 2018</h2><p>Each candidate was fitted on 2017 orders. This old selection used average precision; the revised protocol uses rolling capacity comparisons.</p></div></div><div class="table-scroll"><table class="evidence-table"><thead><tr><th>CANDIDATE</th><th>AVERAGE PRECISION</th><th>ROC AUC</th><th>BRIER SCORE ↓</th></tr></thead><tbody>${Object.entries(report.validation).map(([name,m])=>`<tr><td>${escapeHTML(name.replaceAll('_',' '))}${name===report.selected_model?' <span class="badge">Selected</span>':''}</td><td>${m.average_precision.toFixed(3)}</td><td>${m.roc_auc.toFixed(3)}</td><td>${m.brier_score.toFixed(3)}</td></tr>`).join('')}</tbody></table></div></div><p class="model-label">Selected model: ${escapeHTML(report.selected_model.replaceAll('_',' '))}. Refit on training + validation, then calibrated on May 2018. Test Brier score: ${t.brier_score.toFixed(4)}; constant-prior Brier score: ${report.test_constant_prior.brier_score.toFixed(4)}. Short-promise rule precision at 50/day: ${percent(report.test_short_promise_rule.precision)}.</p>`;
  $('limitations').innerHTML=report.limitations.map(x=>`<li>${escapeHTML(x)}</li>`).join('');
  const gate=document.createElement('div');gate.className='notice';
  gate.innerHTML=`<strong>Research only</strong><span>At 50 reviews/day, the model finds ${c.late_found} late orders; the short-promise rule finds ${report.test_short_promise_rule.late_found}. ${report.release_gate.beats_short_promise_rule_at_50?'Historical evidence still requires prospective validation.':'The model does not beat this simple rule. It is not recommended for operational adoption.'}</span>`;
  $('evidence-content').prepend(gate);
}
async function start(){
  try {
    metadata=await api('/model');$('connection').textContent='Trained model connected';
    const states=['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'];
    document.querySelectorAll('.state').forEach(select=>{select.innerHTML=states.map(s=>`<option ${s===select.dataset.default?'selected':''}>${s}</option>`).join('');});
    $('categories').innerHTML=metadata.known_categories.primary_category.map(c=>`<option value="${escapeHTML(c)}" ${c==='health_beauty'?'selected':''}>${escapeHTML(c.replaceAll('_',' '))}</option>`).join('');
    const [demo, report]=await Promise.all([api('/demo-orders'),api('/evaluation')]);renderEvidence(report);await updateQueue(demo.orders);
  }catch(e){$('connection').textContent='Model unavailable';showError(e);$('orders').innerHTML='<tr><td colspan="6">Predictions unavailable. Check the model setup.</td></tr>';}
}
start();
