'use strict';
// Read availability/prices and open the basket; never submit contact details or a booking.
const {chromium}=require('playwright');
const {PNG}=require('pngjs');
const fs=require('node:fs');
const path=require('node:path');
const base=(process.argv[2]||'https://best-season-sfnvsd24.amvera.io').replace(/\/$/, '');
const out=process.argv[3]||'tmp/pravki-05-10/cart-final';
const local=process.argv.includes('--local');
const root=path.resolve(__dirname,'..');
const date=offset=>{const d=new Date();d.setUTCDate(d.getUTCDate()+offset);return String(d.getUTCDate()).padStart(2,'0')+String(d.getUTCMonth()+1).padStart(2,'0')+d.getUTCFullYear()};

(async()=>{
  const browser=await chromium.launch({channel:'msedge'}),results=[];fs.mkdirSync(out,{recursive:true});
  try {for(const width of [1440,390]){
    const context=await browser.newContext({viewport:{width,height:1000},deviceScaleFactor:1,isMobile:width===390,hasTouch:width===390});
    await context.addInitScript(()=>{try { localStorage.setItem('bs-cookie-consent-v1','dismissed'); } catch (_) {}});
    await context.route('**/*',r=>{
      const url=r.request().url();
      if(local){
        if(/\/css\/kontur-booking(?:\.[a-f0-9]+)?\.css/.test(url))return r.fulfill({contentType:'text/css',body:fs.readFileSync(path.join(root,'config/static/css/kontur-booking.css'),'utf8')});
        if(/\/js\/kontur-style(?:\.[a-f0-9]+)?\.js/.test(url))return r.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(root,'config/static/js/kontur-style.js'),'utf8')});
      }
      if(r.request().method()==='GET'||/^https:\/\/bookonline24\.ru\/widget\/api\/v1\/(?:availabilities\/|daily\/[^/]+\/accommodation-prices(?:\/all)?$)/.test(url))return r.continue();
      return r.abort();
    });
    const page=await context.newPage();await page.goto(base+'/');await page.locator('[data-booking-open]:visible').first().click();
    const form=page.locator('#BookingFormWidget');await form.locator('[data-tid=DateRangePicker__start]').waitFor();
    await form.locator('[data-tid=DateRangePicker__start]').click();await page.keyboard.type(date(9));
    await form.locator('[data-tid=DateRangePicker__end]').click();await page.keyboard.type(date(10));
    await form.getByRole('button',{name:'Проверить наличие'}).click();
    const portals=page.locator('body > .react-ui');
    await portals.getByRole('button',{name:'Выбрать',exact:true}).first().click();
    await portals.getByRole('button',{name:/номер.*ноч/}).first().click();
    const cart=page.locator('[data-bs-booking-cart]');await cart.waitFor();
    const geometry=await cart.evaluate(e=>{
      const frame=e.firstElementChild,sticky=e.querySelector('[data-tid="Sticky__root"]');
      const header=sticky?sticky.firstElementChild:e.querySelector('[data-tid="ModalHeader__root"]').parentElement;
      const f=frame.getBoundingClientRect(),close=e.querySelector('[data-tid="modal-close"]'),c=close.getBoundingClientRect(),s=close.querySelector('svg').getBoundingClientRect();
      return {frame:f.toJSON(),radius:getComputedStyle(frame).borderTopLeftRadius,headerRadius:getComputedStyle(header).borderTopLeftRadius,close:{width:c.width,height:c.height,dx:s.x+s.width/2-c.x-c.width/2,dy:s.y+s.height/2-c.y-c.height/2},overflow:document.documentElement.scrollWidth>innerWidth,blank:[...e.querySelectorAll('input:not([type=hidden]),textarea')].filter(e=>!['checkbox','radio'].includes(e.type)).every(e=>!e.value)};
    });
    const png=PNG.sync.read(await page.screenshot({path:path.join(out,`cart-top-${width}.png`),clip:{x:geometry.frame.x,y:Math.max(0,geometry.frame.y),width:geometry.frame.width,height:170}}));
    const cream=[247,240,230],corner=(x)=>!cream.every((v,j)=>Math.abs(png.data[x*4+j]-v)<2);
    const pass=!geometry.overflow&&geometry.blank&&geometry.close.width===52&&geometry.close.height===52&&Math.abs(geometry.close.dx)<.1&&Math.abs(geometry.close.dy)<.1&&(width===390||(geometry.radius==='40px'&&geometry.headerRadius==='40px'&&corner(0)&&corner(png.width-1)));
    await cart.locator('[data-tid="modal-close"]').click();await cart.waitFor({state:'hidden'});
    results.push({width,...geometry,pass,closed:true});await context.close();
  }}finally{await browser.close();}
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));if(results.some(r=>!r.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
