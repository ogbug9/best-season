// Run with node --test core/tests_analytics.cjs; no network.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../config/static/js/analytics.js'), 'utf8');

function fixture(options = {}) {
  const events = {}, windowEvents = {}, scripts = [], idle = [];
  const attrs = {};
  if(options.form) attrs['data-form-success'] = options.form;
  if(options.house) attrs['data-house-slug'] = options.house;
  const document = {
    readyState: options.loading ? 'interactive' : 'complete',
    documentElement:{scrollHeight:4000},
    body: {classList:{contains:c => c === options.pageClass}, getAttribute:k => attrs[k] || null, removeAttribute:k => delete attrs[k]},
    getElementById(id) {
      if (id === 'metrika-id') return options.noCounter ? null : {textContent:'"12345678"'};
      if (id === 'analytics-config') return {textContent:JSON.stringify({telegramUrl:'https://example.org/chat',whatsappUrl:'https://example.org/wa'})};
      return null;
    },
    createElement: () => ({}), head:{appendChild:script => scripts.push(script)},
    addEventListener:(name, fn) => events[name] = fn,
  };
  const replacements = [];
  const window = {
    localStorage:{getItem() {if(options.storageError) throw new Error('blocked'); return options.consent;}},
    location:{href:options.url || 'https://example.org/?form=ok&ft=fallback&x=1#anchor'},
    scrollY:0, innerHeight:800,
    history:{state:{saved:true},replaceState:(state,title,url) => replacements.push({state,url})},
    addEventListener:(name,fn) => { (windowEvents[name] ||= []).push(fn); },
    removeEventListener:(name,fn) => {windowEvents[name] = (windowEvents[name] || []).filter(f => f !== fn);},
    requestIdleCallback:fn => idle.push(fn),
  };
  if(options.noIdle) delete window.requestIdleCallback;
  const context = vm.createContext({document,window,URL});
  function run() {vm.runInContext(source,context);}
  function flush() {while(idle.length) idle.shift()();}
  function emit(name) {(windowEvents[name] || []).slice().forEach(fn => fn());}
  run();
  return {window,scripts,replacements,attrs,run,flush,emit,
    consent(value) {events['bs:cookie-consent']({detail:value});},
    click(href,place='other') {
      const link = {href,matches:selector => place === 'route' && selector === '[data-directions-link]',closest:selector => ({fallback:'[data-booking-fallback]',header:'header',footer:'footer',contacts:'.contacts, .contacts-section'})[place] === selector};
      events.click({target:{closest:() => link}});
    },
    goals() {return Array.from(window.dataLayer || []);},
    queue() {return Array.from(window.ym?.a || [],args => Array.from(args));},
  };
}

test('no agreement, dismissal and unavailable storage never load Metrika or define ym', () => {
  for(const options of [{},{consent:'dismissed'},{storageError:true}]) {
    const f=fixture(options); f.emit('load'); f.flush(); f.consent('dismissed'); f.flush();
    assert.equal(f.scripts.length,0); assert.equal(f.window.ym,undefined);
  }
});
test('accepted agreement waits for load and idle and inserts one script/init', () => {
  const f=fixture({loading:true}); f.consent('accepted'); f.flush();
  assert.equal(f.scripts.length,0); assert.equal(f.window.ym,undefined);
  f.emit('load'); assert.equal(f.scripts.length,0); f.flush();
  f.consent('accepted'); f.emit('load'); f.flush();
  assert.equal(f.scripts.length,1); assert.equal(f.scripts[0].src,'https://mc.yandex.ru/metrika/tag.js');
  const init=f.queue().filter(args => args[1] === 'init');
  assert.equal(init.length,1); assert.equal(init[0][0],12345678);
  assert.deepEqual(JSON.parse(JSON.stringify(init[0][2])), {webvisor:true,clickmap:true,trackLinks:true,accurateTrackBounce:true,ecommerce:'dataLayer'});
});
test('saved consent loads after idle; empty counter never loads', () => {
  const f=fixture({consent:'accepted'}); f.flush(); assert.equal(f.scripts.length,1);
  const empty=fixture({consent:'accepted',noCounter:true}); empty.flush(); assert.equal(empty.scripts.length,0);
});
test('without idle API script still waits for load', () => {
  const f=fixture({consent:'accepted',loading:true,noIdle:true}); assert.equal(f.scripts.length,0);
  f.emit('load'); assert.equal(f.scripts.length,1);
});
test('dismissal before idle cancels the pending start', () => {
  const f=fixture({consent:'accepted'}); f.consent('dismissed'); f.flush(); assert.equal(f.scripts.length,0);
  f.consent('accepted'); f.flush(); assert.equal(f.scripts.length,1);
});
test('server success counts once, removes query flags, preserves query/hash/history and waits for consent', () => {
  const f=fixture({form:'fallback'});
  assert.deepEqual(f.goals().map(e=>e.event),['form_submitted','booking_fallback_submitted']);
  assert.deepEqual(JSON.parse(JSON.stringify(f.goals()[0].params)),{form_type:'fallback'});
  assert.deepEqual(f.replacements,[{state:{saved:true},url:'/?x=1#anchor'}]);
  assert.equal(f.attrs['data-form-success'],undefined); assert.equal(f.window.ym,undefined);
  f.consent('accepted'); f.flush();
  assert.equal(f.queue().filter(args=>args[1] === 'reachGoal').length,2);
  f.consent('accepted'); f.flush(); assert.equal(f.queue().filter(args=>args[2] === 'form_submitted').length,1);
  f.run(); assert.equal(f.goals().filter(e=>e.event === 'form_submitted').length,1);
});
test('other forms do not count fallback; rejected form has no goal', () => {
  const f=fixture({form:'transfer'}); assert.deepEqual(f.goals().map(e=>e.event),['form_submitted']);
  const invalid=fixture(); assert.equal(invalid.goals().length,0); assert.equal(invalid.replacements.length,0);
});
test('contact goals carry only channel and placement, including configured custom URLs', () => {
  const f=fixture();
  for(const [url,place,channel] of [['tel:+79990000000','header','phone'],['https://t.me/test','footer','telegram'],['https://wa.me/79990000000','fallback','whatsapp'],['https://example.org/chat','contacts','telegram'],['https://example.org/wa','other','whatsapp']]) {
    f.click(url,place); assert.deepEqual(JSON.parse(JSON.stringify(f.goals().at(-1).params)),{channel,place});
  }
  f.click('https://example.org/unrelated'); assert.equal(f.goals().length,5);
});
test('contacts page maps its links to contacts', () => {
  const f=fixture({pageClass:'page-contacts'}); f.click('tel:+79990000000'); assert.equal(f.goals()[0].params.place,'contacts');
});
test('directions view is queued once and delivered after agreement', () => {
  const f=fixture({pageClass:'page-directions'}); assert.equal(f.goals()[0].event,'directions_view');
  f.consent('accepted'); f.flush(); assert.equal(f.queue().filter(args=>args[2] === 'directions_view').length,1);
});
test('house reading reaches 75 percent once with slug', () => {
  const f=fixture({house:'domik-1'}); f.window.scrollY=2199; f.emit('scroll'); assert.equal(f.goals().length,0);
  f.window.scrollY=2200; f.emit('scroll'); assert.equal(f.goals().length,0);
  f.window.scrollY=2201; f.emit('scroll'); f.emit('scroll'); f.emit('load');
  assert.equal(f.goals().length,1); assert.equal(f.goals()[0].event,'house_scroll_75'); assert.equal(f.goals()[0].params.house,'domik-1');
});

test('route click has its own consent-gated goal', () => { const f=fixture(); f.click('https://yandex.ru/maps/?rtext=x', 'route'); assert.equal(f.goals()[0].event,'directions_click'); assert.equal(f.window.ym,undefined); f.consent('accepted'); f.flush(); assert.equal(f.queue().filter(args=>args[2] === 'directions_click').length,1); });
