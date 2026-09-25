// Browser regression fixture. Run node core/tests_booking_layers.cjs and open
// http://127.0.0.1:8766/ at desktop/mobile sizes. Uses the real integration scripts;
// only the SDK/network boundary is replaced, with portal markup seen on the live site.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = `<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/config/static/css/main.css">
<link rel="stylesheet" href="/config/static/css/kontur-booking.css">
<title>Booking layer regression</title>
<style>.test-panel{padding:24px}.test-panel button{margin:8px;padding:12px}.test-overlay{position:fixed;inset:0;background:#0008;display:grid;place-items:center}.test-dialog{background:white;padding:20px;max-width:90vw}.test-popup{background:white;position:fixed;top:150px;left:5%;padding:16px;max-width:90vw}</style>
<body><main class="test-panel"><button data-booking-open>Открыть бронирование</button><output id="results">Готово к проверке</output></main>
<div id="already-inert" inert></div>
<div class="react-ui" data-rendered-container-id="datepicker"></div>
<dialog class="booking-modal booking-system" data-booking-modal aria-label="Бронирование">
<div class="booking-modal__inner test-panel"><button data-booking-close>Закрыть внешнее</button>
<h2 class="booking-modal__title">Бронирование</h2>
<div data-booking-host id="BookingFormWidget" hidden></div>
<div data-booking-catalog hidden><div data-kontur-type="roomsList" id="rooms"></div></div>
<p data-booking-loading hidden>Загрузка</p><div data-booking-fallback hidden>Резервная форма</div>
<p data-booking-note></p></div></dialog>
<script id="booking-config" type="application/json">{"hotelId":"fixture"}</script>
<script>
let sequence=0, initCount=0, datePickerReopened=false; const results=[];
function record(label, pass){results.push((pass?'PASS ':'FAIL ')+label);document.getElementById('results').textContent=results.join(' | ');}
function frame(fn){requestAnimationFrame(()=>requestAnimationFrame(fn));}
function openPortal(owner, popup=false, unannotated=false){
 const portal=document.createElement('div');portal.className='react-ui';
 let marker=null;
 if(!unannotated){
  // Kontur normally links a portal to its owner via a noscript marker + matching id.
  const id='fixture-'+(++sequence); marker=document.createElement('noscript');marker.setAttribute('data-render-container-id',id);owner.append(marker);
  portal.setAttribute('data-rendered-container-id',id);
 }
 // Some real screens (the availability result, and the date picker opened from it)
 // mount a .react-ui root with NEITHER the marker NOR the id attribute — this is
 // the case that used to be silently dropped from the active-portal list.
 portal.innerHTML=popup?'<div class="test-popup" style="z-index: 10002"><button>Выбрать дату</button></div>':'<div class="test-overlay" style="z-index: 9000"><div class="test-dialog" data-tid="modal-content" role="dialog" aria-modal="true"><button>Закрыть внутреннее</button><input aria-label="Гость"><button>Открыть календарь</button><button data-day-pick>День 12</button></div></div>';
 document.body.append(portal);
 // Picking a day in the real widget redraws the grid — a childList mutation that
 // transiently moves focus off the DOM (activeElement reverts to body) even though
 // the same dialog stays open. Our sync() used to treat that exactly like a brand
 // new dialog appearing and yank focus back to the FIRST control every time,
 // which is what snapped the calendar back to its opening date and trapped
 // guests who could only escape by closing the whole thing.
 var dayPick = portal.querySelector('[data-day-pick]');
 if (dayPick) dayPick.onclick = function () {
   dayPick.focus();
   dayPick.blur();
   var marker = document.createElement('span');
   portal.querySelector('[data-tid="modal-content"]').appendChild(marker);
   marker.remove();
   frame(function () {
     var stolen = document.activeElement === portal.querySelector('button');
     record('focus not re-stolen to first control after a same-dialog redraw', !stolen);
   });
 };
 const close=()=>{document.removeEventListener('keydown',escape);portal.remove();if(marker)marker.remove();setTimeout(()=>{
  const outer=document.querySelector('dialog');
  // The permanent, empty datepicker placeholder is always present — exclude
  // it, it carries no active content and closing never touches it.
  const stillOpen=Array.from(document.querySelectorAll('.react-ui')).some(el=>el!==document.querySelector('[data-rendered-container-id="datepicker"]'));
  // Leaving vendor mode now waits out a short grace window (see
  // "Переключение полей" above) in case Kontur is about to swap in a new
  // popup rather than actually being done — real close needs to wait past it.
  if(!stillOpen){record('outer modality restored',outer.matches(':modal'));record('focus restored',outer.contains(document.activeElement));record('still initialized once',initCount===1);}
 },350);};
 const escape=e=>{if(e.key==='Escape' && portal===Array.from(document.querySelectorAll('.react-ui')).pop()){e.preventDefault();e.stopImmediatePropagation();close();}};
 document.addEventListener('keydown',escape);
 portal.querySelector('button').onclick=close;
 if(!popup)portal.querySelectorAll('button')[1].onclick=()=>openPortal(portal,true);
 frame(()=>{const outer=document.querySelector('dialog'), button=portal.querySelector('button'),r=button.getBoundingClientRect();
 record('outer left top layer',!outer.matches(':modal')&&outer.open);
 record('inner receives pointer',button.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)));
 record('no horizontal overflow',document.documentElement.scrollWidth<=innerWidth);
 if(!popup)record('focus in inner',portal.contains(document.activeElement));
 });
}
window.HotelWidget={init(c){initCount++;c.hooks.onInit();},add(c){if(c.type==='bookingForm'){
 const host=document.getElementById(c.appearance.container);
 host.innerHTML='<button>Проверить наличие</button><button>Посмотреть номер</button><button>Даты</button><button>Результат наличия (без метки)</button><button data-tid="DateRangePicker__start">Поле даты</button><button>Переключение полей</button><button data-tid="DateRangePicker__end">Поле выезда</button><button>Возврат фокуса после выбора дат</button>';
 host.querySelectorAll('button').forEach((b,i)=>{if(i<5)b.onclick=()=>openPortal(host,i===2,i===3);});
 // Live bug: the SDK closes its calendar when a date is picked; our exit
 // path returned focus to the date field, the SDK reopened the calendar on
 // that focus, and the picker kept coming back. Focus must go on to the
 // search button instead.
 host.querySelectorAll('button')[7].onclick=function(){
  const endField=host.querySelector('[data-tid="DateRangePicker__end"]');
  endField.focus();
  const portal=document.createElement('div'); portal.className='react-ui';
  portal.innerHTML='<div data-tid="DateRangePicker__root" style="position:absolute;top:200px;left:20px;width:200px;height:200px;background:white"><button data-date-range-picker-day="20.10.2026">20</button></div>';
  document.body.appendChild(portal);
  setTimeout(()=>{
   portal.remove();
   setTimeout(()=>{
    record('focus does not return to a date field after the calendar closes', document.activeElement!==endField && !document.activeElement.closest('[data-tid^="DateRangePicker"]'));
    record('focus moves on to the search button', document.activeElement===host.querySelector('button'));
   },450);
  },200);
 };
 // The date-picker portal is mounted ONCE, empty, before anyone opens the
 // modal — invisible to our own visibility check for as long as it stays
 // empty. This mirrors what a plain "Заезд"/"Выезд" field's own calendar
 // does in production: Kontur pre-mounts the container and only fills it
 // in on click. If that empty container ever got marked inert while empty,
 // the click that should reveal it would be silently swallowed (inert
 // blocks pointer events on the whole subtree) — a permanent deadlock,
 // since it can never look "active" to us again once nothing can click it.
 host.querySelectorAll('button')[4].onclick=function(){
  const field=document.querySelector('[data-rendered-container-id="datepicker"]');
  // Live mobile failure: SDK absolute popup uses viewport coordinates,
  // but the body's scroll lock shifts it 912px above those coordinates.
  document.body.style.top='-912px';
  field.innerHTML='<div data-tid="DateRangePicker__root" style="position:absolute;top:'+ (innerHeight-300) +'px;left:20px;width:260px;height:466px;z-index:5000;background:white">'
   +'<div data-tid="PopupContent" style="position:relative;height:100%;overflow:hidden">'
   +'<button id="pick-day-in-field" data-date-range-picker-day="12.10.2026">12</button>'
   +'<button id="pick-second-day" data-date-range-picker-day="14.10.2026">14</button>'
   +'<button id="pick-last-day" style="position:absolute;top:430px;left:20px">31</button></div></div>';
  // Per the file header: Kontur's RenderContainer re-appends a portal to the
  // end of body on every render, so a real reveal also moves it there.
  document.body.appendChild(field);
  frame(()=>{
   const btn=document.getElementById('pick-day-in-field'), r=btn.getBoundingClientRect();
   record('pre-mounted field portal is clickable once revealed', !btn.inert && btn.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)));
   setTimeout(()=>{
    const picker=field.querySelector('[data-tid="DateRangePicker__root"]');
    const bottom=picker.getBoundingClientRect().bottom;
    record('popup stays in viewport despite a scrolled body', picker.getBoundingClientRect().top>=8 && getComputedStyle(picker).position==='fixed');
    record('date-range popup fits below viewport edge on every viewport', bottom<=innerHeight-6 && picker.style.maxHeight!=='' && picker.style.overflowY==='auto');
    const content=picker.querySelector('[data-tid="PopupContent"]');
    record('vendor popup content becomes scrollable', content.style.overflowY==='auto' && content.scrollHeight>content.clientHeight);
    content.scrollTop=content.scrollHeight-content.clientHeight;
    const last=document.getElementById('pick-last-day'), lastRect=last.getBoundingClientRect();
    record('last calendar row is reachable by scrolling', lastRect.bottom<=innerHeight && last.contains(document.elementFromPoint(lastRect.x+lastRect.width/2,lastRect.y+lastRect.height/2)));
   },650);
   if(datePickerReopened) return;
   // Date selection must not disappear after 400ms. An explicit outside
   // click closes the field calendar, and the same field reopens it.
   document.getElementById('pick-day-in-field').click();
   setTimeout(()=>document.getElementById('pick-second-day').click(),150);
   setTimeout(()=>record('date-range popup still open mid-pick',
     !document.querySelector('[data-rendered-container-id="datepicker"]').hidden),300);
   setTimeout(()=>{
    host.querySelector('[data-tid="DateRangePicker__end"]').click();
    const container=document.querySelector('[data-rendered-container-id="datepicker"]');
    const marker=document.createElement('span'); container.appendChild(marker); marker.remove();
   },450);
   setTimeout(()=>record('date-range popup survives field switch without an early hide',
     !document.querySelector('[data-rendered-container-id="datepicker"]').hidden),700);
   setTimeout(()=>document.getElementById('pick-second-day').click(),750);
   setTimeout(()=>{
    record('calendar remains open after a pause between date choices', !field.hidden);
    document.querySelector('.booking-modal__title').click();
    record('outside click closes only the calendar', field.hidden && document.querySelector('dialog').open);
   },1250);
   setTimeout(()=>{
    datePickerReopened=true;
    host.querySelectorAll('button')[4].click();
    frame(()=>record('date-range popup can reopen after dismissal',
      !document.querySelector('[data-rendered-container-id="datepicker"]').hidden));
   },1300);
  });
 };
 // Confirmed live on best-season-sfnvsd24.amvera.io: picking "Заезд" doesn't
 // just redraw Kontur's range-picker popup — it TEARS DOWN the whole
 // .react-ui container. A new one only appears once the guest clicks
 // "Выезд". Exiting vendor mode (back to a native showModal()) the instant
 // portals() is momentarily empty, then re-entering the moment the new
 // container shows up, is a visible close-then-reopen flash — reported live
 // as "не успеваю нажать на Выезд, всё закрывается". The fix gives the exit
 // a short grace window instead of acting on the gap immediately.
 host.querySelectorAll('button')[5].onclick=function(){
  const outer=document.querySelector('dialog');
  let flickered=false;
  const poll=setInterval(()=>{ if(outer.matches(':modal')) flickered=true; },10);
  const a=document.createElement('div'); a.className='react-ui';
  a.innerHTML='<button data-date-range-picker-day="a" style="position:fixed;top:250px;left:20px">A</button>';
  document.body.appendChild(a);
  frame(()=>{
   record('entered vendor mode for the first popup', !outer.matches(':modal')&&outer.open);
   // Kontur destroys container A almost immediately after the pick.
   setTimeout(()=>{
    a.remove();
    // The guest clicks "Выезд" well inside the grace window — container B
    // appears before the delayed exit would have fired.
    setTimeout(()=>{
     const b=document.createElement('div'); b.className='react-ui';
     b.innerHTML='<button data-date-range-picker-day="b" style="position:fixed;top:250px;left:20px">B</button>';
     document.body.appendChild(b);
     setTimeout(()=>{
      clearInterval(poll);
      record('no dialog flicker while Kontur tears down and recreates the popup between Заезд/Выезд', !flickered);
      // Now genuinely finish: remove B and don't recreate anything — this
      // time the grace window should elapse and modality should restore.
      b.remove();
      setTimeout(()=>record('outer modality restored once nothing reappears after the grace window',
        outer.matches(':modal')), 500);
     }, 200);
    }, 150);
   }, 20);
  });
 };
}}};
</script>
<script src="/config/static/js/booking-layers.js"></script><script src="/config/static/js/kontur.js"></script></body></html>`;
const allowed = new Set(['/config/static/css/main.css', '/config/static/css/kontur-booking.css', '/config/static/js/booking-layers.js', '/config/static/js/kontur.js']);
http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  if (url === '/') { res.setHeader('Content-Type', 'text/html; charset=utf-8'); return res.end(html); }
  if (!allowed.has(url)) { res.writeHead(404); return res.end(); }
  res.setHeader('Content-Type', url.endsWith('.js') ? 'text/javascript; charset=utf-8' : 'text/css; charset=utf-8');
  res.end(fs.readFileSync(path.join(root, url)));
}).listen(Number(process.argv[2]) || 8766, '127.0.0.1', function () {
  console.log('Layer regression: http://127.0.0.1:' + this.address().port + '/');
});
