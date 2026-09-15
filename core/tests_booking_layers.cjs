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
<dialog class="booking-modal booking-system" data-booking-modal aria-label="Бронирование">
<div class="booking-modal__inner test-panel"><button data-booking-close>Закрыть внешнее</button>
<h2 class="booking-modal__title">Бронирование</h2>
<div data-booking-host id="BookingFormWidget" hidden></div>
<div data-booking-catalog hidden><div data-kontur-type="roomsList" id="rooms"></div></div>
<p data-booking-loading hidden>Загрузка</p><div data-booking-fallback hidden>Резервная форма</div>
<p data-booking-note></p></div></dialog>
<script id="booking-config" type="application/json">{"hotelId":"fixture"}</script>
<script>
let sequence=0, initCount=0; const results=[];
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
 portal.innerHTML=popup?'<div class="test-popup" style="z-index: 10002"><button>Выбрать дату</button></div>':'<div class="test-overlay" style="z-index: 9000"><div class="test-dialog" data-tid="modal-content" role="dialog" aria-modal="true"><button>Закрыть внутреннее</button><input aria-label="Гость"><button>Открыть календарь</button></div></div>';
 document.body.append(portal);
 const close=()=>{document.removeEventListener('keydown',escape);portal.remove();if(marker)marker.remove();frame(()=>{
  const outer=document.querySelector('dialog');
  if(!document.querySelector('.react-ui')){record('outer modality restored',outer.matches(':modal'));record('focus restored',outer.contains(document.activeElement));record('still initialized once',initCount===1);}
 });};
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
 host.innerHTML='<button>Проверить наличие</button><button>Посмотреть номер</button><button>Даты</button><button>Результат наличия (без метки)</button>';
 host.querySelectorAll('button').forEach((b,i)=>b.onclick=()=>openPortal(host,i===2,i===3));
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
}).listen(8766, '127.0.0.1', () => console.log('Layer regression: http://127.0.0.1:8766/'));
