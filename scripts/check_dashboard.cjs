const fs=require('node:fs');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const root=require('node:path').resolve(__dirname,'..');
const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const dom=new JSDOM(fs.readFileSync(root+'/app/static/index.html','utf8'),{url:'http://localhost',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;
w.fetch=async(path,options)=>{
 let data=structuredClone(fixture[path]);
 if(path==='/predict/batch'){
  const budget=JSON.parse(options.body).investigation_budget;
  data.selected=Math.min(budget,data.orders.length);
  data.orders.forEach((r,i)=>r.selected_for_review=i<budget);
 }
 return {ok:true,json:async()=>data};
};
w.eval(fs.readFileSync(root+'/app/static/app.js','utf8'));
async function settle(){for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));}
(async()=>{
 await settle();
 assert.equal(w.document.getElementById('orders').querySelectorAll('tr').length,12);
 assert.equal(w.document.getElementById('order-count').textContent,'12');
 assert.equal(w.document.getElementById('selected-count').textContent,'5');
 assert.equal(w.document.getElementById('error').hidden,true);
 w.document.getElementById('budget').value='3';w.document.getElementById('refresh').click();await settle();
 assert.equal(w.document.getElementById('selected-count').textContent,'3');
 w.document.querySelector('[data-view="evidence"]').click();
 assert.equal(w.document.getElementById('evidence').hidden,false);
 assert.match(w.document.getElementById('evidence-content').textContent,/does not beat this simple rule/);
 w.document.querySelector('[data-view="predict"]').click();
 w.document.getElementById('predict-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await settle();
 assert.match(w.document.getElementById('result').textContent,/relative risk/);
 w.document.querySelector('[data-view="queue"]').click();
 w.document.getElementById('budget').value='0';w.document.getElementById('refresh').click();await settle();
 assert.equal(w.document.getElementById('error').hidden,false);
 assert.match(w.document.getElementById('error').textContent,/whole-number/);
 console.log('PASS: initial queue, review budget, evidence view, single-order form, invalid-budget error');
 dom.window.close();
})().catch(e=>{console.error(e);process.exit(1)});
