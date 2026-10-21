const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../config/static/js/calendar.js'), 'utf8');

function fixture(saved) {
  const events = {}, requests = [], timers = new Map(), nodes = {};
  let seq = 0;
  const months = {addEventListener(k, fn) { this[k] = fn; }, innerHTML: '',
    querySelectorAll:()=>[], querySelector:()=>null, setAttribute(){},removeAttribute(){},contains:()=>false};
  const book = {disabled: false};
  const rows = {};
  for (const [key, min, max, value] of [['adults',1,4,2],['children',0,4,0],['pets',0,1,0]]) {
    const output = {textContent: String(value)};
    const row = rows[key] = {dataset: {counter:key,min,max}, querySelector:()=>output};
    row.buttons = [-1,1].map(step=>({dataset:{step}, closest:()=>row}));
    row.querySelectorAll = ()=>row.buttons;
  }
  const fields = Object.fromEntries(['house','date_from','date_to','guests','children','pets'].map(k=>[k,{value:''}]));
  const panel = {
    dataset:{house:'house', houseId:'28', capacity:'4',calendarUrl:'/calendar',priceUrl:'/price'},
    addEventListener(k,fn){events['panel:'+k]=fn;},
    querySelectorAll:s=>s==='[data-booking-open]' ? [book] : [],
    querySelector(selector){
      if(selector==='[data-calendar-months]') return months;
      const key = selector.match(/data-counter="(\w+)"/);
      if(key) return selector.includes('[data-value]') ? rows[key[1]].querySelector() : rows[key[1]];
      return nodes[selector] ||= {textContent:'',hidden:true,value:''};
    }
  };
  const document = {
    querySelector:s=>s==='[data-booking-panel]' ? panel : {elements:fields},
    addEventListener(k,fn){events[k]=fn;}
  };
  vm.runInNewContext(source, {
    document, window:{matchMedia:()=>({matches:false})}, Date, Intl,
    sessionStorage:{getItem:()=>saved ? JSON.stringify(saved) : null, setItem(){}},
    setTimeout(fn){timers.set(++seq,fn);return seq;}, clearTimeout(id){timers.delete(id);},
    fetch(url){return new Promise(resolve=>requests.push({url,resolve}));}
  });
  return {fields, nodes, months, rows, requests, book,
    pick(day){months.click({target:{closest:s=>s==='[data-day]' ? {dataset:{day}} : null}});},
    step(key, index=1){events['panel:click']({target:{closest:s=>s==='[data-step]' ? rows[key].buttons[index] : null}});},
    field(key){events['panel:click']({target:{closest:s=>s==='[data-field]' ? {dataset:{field:key}} : null}});},
    navigate(start){months.click({target:{closest:s=>s==='[data-day]' ? null : {dataset:{start}}}});},
    open(){const e={detail:{button:{hasAttribute:()=>false}},preventDefault(){this.cancelled=true;}};events['booking:prepare'](e);return !e.cancelled;},
    tick(){const tasks=[...timers.values()];timers.clear();tasks.forEach(fn=>fn());},
  };
}
const flush = ()=>new Promise(resolve=>setImmediate(resolve));

test('new arrival clears old departure; house, children and pets transfer through any entry',()=>{
  const f=fixture(); f.pick('2099-09-28');f.pick('2099-09-30'); f.open();
  assert.equal(f.fields.date_to.value,'2099-09-30');
  f.pick('2099-10-05');f.step('children');f.step('pets');f.open();
  assert.equal(f.fields.date_to.value,'');assert.equal(f.fields.house.value,'28');
  assert.equal(f.fields.guests.value,3);assert.equal(f.fields.children.value,1);assert.equal(f.fields.pets.value,1);
});
test('capacity prevents fifth guest and blocks invalid restored selections',()=>{
  const f=fixture();f.step('adults');f.step('adults');f.step('children');f.open();
  assert.equal(f.fields.guests.value,4);assert.equal(f.rows.children.buttons[1].disabled,true);
  const restored=fixture({adults:4,children:1,pets:0});
  assert.equal(restored.book.disabled,true);assert.equal(restored.open(),false);
  restored.step('adults',0);assert.equal(restored.open(),true);
});
test('stale quote and calendar responses cannot overwrite current selection',async()=>{
  const f=fixture();f.pick('2099-09-28');f.navigate('2099-09-01');f.tick();
  f.pick('2099-09-30');f.navigate('2099-10-01');f.tick();
  const prices=f.requests.filter(r=>r.url.startsWith('/price'));
  const calendars=f.requests.filter(r=>r.url.startsWith('/calendar'));
  prices[1].resolve({json:async()=>({total:200,date_from:'2099-09-28',date_to:'2099-09-30'})});
  calendars[1].resolve({text:async()=>'new'});await flush();
  prices[0].resolve({json:async()=>({total:100,date_from:'2099-09-28',date_to:''})});
  calendars[0].resolve({text:async()=>'old'});await flush();
  assert.equal(f.nodes['[data-total]'].textContent,'200 ₽');assert.equal(f.months.innerHTML,'new');
});
test('new selection invalidates a quote during debounce',async()=>{
  const f=fixture();f.pick('2099-09-28');f.tick();f.pick('2099-09-30');
  f.requests.find(r=>r.url.startsWith('/price')).resolve({json:async()=>({total:100})});
  await flush();assert.equal(f.nodes['[data-total]'].textContent,'Уточняем расчёт…');
});
test('oversized date range blocks all panel entry requests',()=>{
  const f=fixture();f.pick('2099-01-01');f.pick('2099-04-01');
  assert.equal(f.book.disabled,true);assert.equal(f.open(),false);
});

test('checkout field edits checkout instead of starting a new range',()=>{
  const f=fixture();f.pick('2099-09-28');f.pick('2099-09-30');
  f.field('date_to');f.pick('2099-10-02');f.open();
  assert.equal(f.fields.date_from.value,'2099-09-28');
  assert.equal(f.fields.date_to.value,'2099-10-02');
  f.field('date_from');f.pick('2099-10-05');f.open();
  assert.equal(f.fields.date_from.value,'2099-10-05');
  assert.equal(f.fields.date_to.value,'');
});

test('picking stays immediate without month requests; malformed saved dates are ignored',()=>{
  const f=fixture({dateFrom:'2099-02-31',dateTo:'2099-03-02'});
  f.pick('2099-09-28');f.pick('2099-09-30');
  assert.equal(f.nodes['[data-input="date_from"]'].value,'2099-09-28');
  assert.equal(f.nodes['[data-input="date_to"]'].value,'2099-09-30');
  assert.equal(f.requests.filter(r=>r.url.startsWith('/calendar')).length,0);
});

test('HTTP errors preserve the calendar and expose a retry message',async()=>{
  const f=fixture();f.months.innerHTML='original grid';f.navigate('2099-10-01');
  f.requests[0].resolve({ok:false,text:async()=>'<h1>Server error</h1>'});await flush();
  assert.equal(f.months.innerHTML,'original grid');
  assert.match(f.nodes['[data-calendar-status]'].textContent,/Не удалось загрузить месяц/);
});

test('server availability error still blocks continuation until selection changes',async()=>{
  const f=fixture();f.pick('2099-09-28');f.pick('2099-09-30');f.tick();
  f.requests.find(r=>r.url.startsWith('/price')).resolve({json:async()=>({error:'Часть выбранных дат занята.'})});await flush();
  assert.equal(f.open(),false);
  f.pick('2099-10-05');assert.equal(f.open(),true);
});
