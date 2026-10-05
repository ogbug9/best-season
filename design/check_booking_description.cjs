// Read-only SDK acceptance; --local substitutes CSS/JS before deployment.
const {chromium}=require('playwright'),fs=require('fs'),assert=require('node:assert/strict');
const local=process.argv.includes('--local');
const base=process.env.BS_CHECK_BASE||'https://best-season-sfnvsd24.amvera.io';
const mode=local?'local':'live';
(async()=>{const b=await chromium.launch({channel:'msedge'});try{for(const width of [1440,390]){
  const p=await b.newPage({viewport:{width,height:1000}}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  await p.route('**/*',r=>{
    const u=r.request().url();
    if(local&&/\/js\/kontur-style(?:\.[a-f0-9]+)?\.js/.test(u))return r.fulfill({contentType:'text/javascript',body:fs.readFileSync('config/static/js/kontur-style.js','utf8')});
    if(local&&/\/css\/kontur-booking(?:\.[a-f0-9]+)?\.css/.test(u))return r.fulfill({contentType:'text/css',body:fs.readFileSync('config/static/css/kontur-booking.css','utf8')});
    if(r.request().method()==='GET'||/^https:\/\/bookonline24\.ru\/widget\/api\/v1\/(?:availabilities\/|daily\/[^/]+\/accommodation-prices(?:\/all)?$)/.test(u))return r.continue();
    return r.abort();
  });
  await p.goto(base+'/');await p.locator('[data-booking-open]:visible').first().click();
  const calendar=p.locator('#BookingCalendarWidget');
  await calendar.locator('.OVAPps').first().waitFor({timeout:45000});
  const calendarState=()=>calendar.evaluate(e=>({height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width,days:e.querySelectorAll('.OVAPps').length,overflow:document.documentElement.scrollWidth>innerWidth}));
  const initial=await calendarState();assert(initial.height<800&&initial.height>100&&initial.days>20&&!initial.overflow);
  const toggles=p.locator('#BookingRoomsWidget [data-bs-description-toggle]');
  await toggles.first().waitFor({timeout:45000});
  for(let i=0;i<4;i++){
    const t=toggles.nth(i),id=await t.getAttribute('aria-controls'),copy=p.locator('#'+id);
    assert.equal(await copy.getAttribute('data-bs-description-compact'),'true');
    assert.equal(await t.evaluate(e=>getComputedStyle(e).borderRadius),'100px');
    await t.click();await p.waitForTimeout(150);
    const state=await copy.evaluate(e=>{
      const original=e.nextElementSibling;
      const norm=s=>s.replace(/Коротко$/,'').replace(/\s*[-•]\s+/g,' ').replace(/\s+/g,' ').trim();
      return {sameText:norm(e.innerText)===norm(original.textContent),headings:e.querySelectorAll('.booking-description-heading').length,items:e.querySelectorAll('li').length,font:getComputedStyle(e).fontSize,line:getComputedStyle(e).lineHeight,hidden:getComputedStyle(original).display==='none',compact:e.getAttribute('data-bs-description-compact'),overflow:document.documentElement.scrollWidth>innerWidth};
    });
    assert(state.sameText&&state.headings>0&&state.items>5&&state.hidden&&state.compact==='false'&&!state.overflow);
    if(i===0){await copy.scrollIntoViewIfNeeded();await p.screenshot({path:`tmp/booking-readable-${mode}-${width}.png`});}
    await t.click();await p.waitForTimeout(150);assert.equal(await copy.getAttribute('data-bs-description-compact'),'true');
    await t.click();await t.click();console.log({width,house:i+1,description:state});
  }
  // The calendar's eye button opens the plain, full room description.
  await calendar.locator('[data-tid="Button__rootElement"]').nth(1).click();
  const detail=p.locator('[data-bs-description-copy][data-bs-room-description]');await detail.waitFor();
  const detailToggle=p.locator('[data-bs-room-description] + [data-bs-description-toggle]');
  assert.equal(await detail.getAttribute('data-bs-description-compact'),'true');await detailToggle.click();await p.waitForTimeout(150);
  const full=await detail.evaluate(e=>({same:e.innerText.replace(/\s*[-•]\s+/g,' ').replace(/\s+/g,' ').trim()===e.nextElementSibling.textContent.replace(/\s*[-•]\s+/g,' ').replace(/\s+/g,' ').trim(),items:e.querySelectorAll('li').length,font:getComputedStyle(e).fontSize,height:e.clientHeight,overflow:document.documentElement.scrollWidth>innerWidth}));
  console.log({width,full});assert(full.same&&full.items>10&&full.height<=360&&!full.overflow);
  await detail.scrollIntoViewIfNeeded();await p.screenshot({path:`tmp/booking-room-detail-${mode}-${width}.png`});
  await detailToggle.click();await detailToggle.click();assert.equal(await detail.count(),1);
  await p.locator('body > .react-ui').getByRole('button',{name:'Закрыть',exact:true}).last().click();
  await p.locator('[data-booking-close]').click();await p.locator('[data-booking-open]:visible').first().click();
  await calendar.locator('.OVAPps').first().waitFor();const reopened=await calendarState();
  assert(reopened.height<800&&reopened.days>20&&!reopened.overflow);
  await p.setViewportSize({width:width===390?430:1920,height:1000});await p.waitForTimeout(250);
  const resized=await calendarState();assert(resized.height<800&&!resized.overflow);
  assert.deepEqual(errors,[]);console.log({width,calendar:{initial,reopened,resized},roomDetail:full,errors});await p.close();
}}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
