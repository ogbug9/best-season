'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {PNG} = require('pngjs');
const reference = require('./pravki_05_10_reference.json');
const normal = s => s.replace(/\s+/g, ' ').trim();
const near = (a,b,t=2) => Math.abs(a-b)<=t;

function renderedLines(e) {
  const groups=new Map(),walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()) {
    const node=walker.currentNode;
    for(let i=0;i<node.length;i++) {
      const range=document.createRange();range.setStart(node,i);range.setEnd(node,i+1);
      const box=range.getBoundingClientRect();if(box.width===0)continue;
      const y=Math.round(box.y);groups.set(y,(groups.get(y)||'')+node.textContent[i]);
    }
  }
  return [...groups.values()].map(s=>s.trim()).filter(Boolean);
}

function ink(png, color, start, end) {
  for(let y=start;y<end;y++) {
    let count=0;
    for(let x=0;x<png.width;x++) {
      const i=(y*png.width+x)*4;
      if(color.every((v,j)=>Math.abs(png.data[i+j]-v)<2)) count++;
    }
    if(count>=3) return y;
  }
  return null;
}

module.exports = async function checkContent(browser, base, out, checks) {
  function record(name,width,pass,detail){checks.push({name,width,pass,detail});}
  for(const width of [1440,390]) {
    const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1,hasTouch:width===390,isMobile:width===390});
    await context.route('**/*',r=>new URL(r.request().url()).origin===base&&r.request().method()!=='POST'?r.continue():r.abort());
    await context.addInitScript(()=>{try{localStorage.setItem('bs-cookie-consent-v1','dismissed')}catch(_){} });
    const page=await context.newPage(), errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    for(const [route,items] of Object.entries(reference)) {
      await page.goto(base+route);await page.evaluate(()=>document.fonts.ready);
      const faq=page.locator('.faq__item');
      record(`FAQ count ${route}`,width,await faq.count()===items.length);
      for(let i=0;i<items.length;i++) {
        const item=faq.nth(i), question=item.locator('.faq__question'),answer=item.locator('.faq__answer');
        const [wantQuestion,wantHtml]=items[i];
        const wantText=await page.evaluate(html=>{const e=document.createElement('div');e.innerHTML=html;return e.textContent},wantHtml.replace(/<\/p>|<\/li>/g,'$& '));
        const actualText=await answer.evaluate(e=>{const copy=document.createElement('div');copy.innerHTML=e.innerHTML.replace(/<\/p>|<\/li>/g,'$& ');return copy.textContent});
        record(`FAQ copy ${route} #${i+1}`,width,normal(await question.innerText())===normal(wantQuestion)&&normal(actualText)===normal(wantText));
        record(`FAQ initial ${route} #${i+1}`,width,(await question.getAttribute('aria-expanded'))===String(i===0));
        if(i>0) await question.click();
        record(`FAQ open ${route} #${i+1}`,width,await answer.isVisible()&&await question.getAttribute('aria-expanded')==='true');
        record(`FAQ open chevron ${route} #${i+1}`,width,await question.evaluate(e=>getComputedStyle(e,'::after').content)==='""');
        await question.focus();await page.keyboard.press('Enter');
        await answer.waitFor({state:'hidden'});
        record(`FAQ keyboard ${route} #${i+1}`,width,!await answer.isVisible()&&await question.getAttribute('aria-expanded')==='false');
        record(`FAQ closed chevron ${route} #${i+1}`,width,await question.evaluate(e=>getComputedStyle(e,'::after').content)==='""');
        await question.click();
      }
      await page.evaluate(()=>document.querySelectorAll('.faq__item').forEach(e=>{e.classList.add('is-open');e.querySelector('.faq__question').setAttribute('aria-expanded','true');e.querySelector('.faq__answer').hidden=false}));
      await page.mouse.move(0,0);await page.evaluate(()=>document.activeElement.blur());
      await page.waitForTimeout(220);
      const header=page.locator('.header');
      await header.evaluateAll(es=>es.forEach(e=>e.style.visibility='hidden'));
      await page.locator('.faq').screenshot({path:path.join(out,`faq-${route==='/'?'home':route.split('/')[1]}-${width}.png`)});
      await header.evaluateAll(es=>es.forEach(e=>e.style.removeProperty('visibility')));
      if(route==='/') {
        const links=await faq.first().locator('a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
        record('FAQ route links',width,links.length===3&&links[0]==='https://yandex.com/maps/-/CPsvELJx'&&links[1].includes('/kak-dobratsya/')&&links[2]==='https://www.tutu.ru/rasp.php?st1=20000&st2=43806',links);
        const directions=await context.request.get(new URL(links[1],base).href);
        record('Directions destination HTTP 200',width,directions.status()===200);
        const paras=page.locator('.about__text > p');
        record('Home updated about',width,!(await paras.allTextContents()).join(' ').includes('богатый и'));
        if(width===1440) record('Home about desktop lines',width,await paras.nth(1).evaluate(e=>e.getBoundingClientRect().height)===216);
      }
      if(route==='/razmeshchenie/') {
        record('Gazebo link',width,await faq.last().locator('a').getAttribute('href')==='/territoriya/uslugi/#service-bolshaya-besedka'&&!(await faq.last().textContent()).includes('гиперссылка'));
        const services=await context.request.get(base+'/territoriya/uslugi/');
        record('Gazebo destination HTTP 200 and anchor',width,services.status()===200&&(await services.text()).includes('id="service-bolshaya-besedka"'));
        if(width===390) {
          const geometry=await page.evaluate(()=>{const button=document.querySelector('.searchbar'),card=document.querySelector('.house');const b=button.getBoundingClientRect(),c=card.getBoundingClientRect();return {gap:c.top-b.bottom,width:c.width,height:c.height}});
          record('Mobile catalogue ratio',width,near(geometry.width/geometry.height,610/500,.01),geometry);
        }
      }
      // Hovering/holding the parent must leave the button's own state alone.
      for(const selector of ['.house','.territory-card','.place','.promo']) {
        const cards=page.locator(selector);
        if(!await cards.count()) continue;
        const card=cards.first(),btn=card.locator('.btn, .house__book, .territory-card__link').first();
        if(!await btn.count()||!await btn.isVisible()) continue;
        await card.scrollIntoViewIfNeeded();await page.mouse.move(0,0);
        const before=await btn.evaluate(e=>getComputedStyle(e).backgroundColor);
        const box=await card.boundingBox();await page.mouse.move(box.x+4,box.y+4);await page.mouse.down();await page.waitForTimeout(250);
        record(`Parent independent ${route} ${selector}`,width,before===await btn.evaluate(e=>getComputedStyle(e).backgroundColor));
        await page.mouse.up();
      }
    }
    if(width===390) {
      await page.goto(base+'/');
      await page.locator('.nav-toggle__button').click();
      record('Mobile menu opens',width,await page.locator('.nav-toggle').evaluate(e=>e.open));
      const menuButtons=page.locator('.nav-toggle [data-button-type]');
      const palette={a:'rgb(73, 73, 73)',b:'rgb(213, 207, 199)',c:'rgb(213, 207, 199)',d:'rgb(155, 80, 38)',e:'rgb(155, 80, 38)',f:'rgb(155, 80, 38)'};
      await page.evaluate(()=>document.querySelector('.nav-toggle').addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation()},true));
      for(let i=0;i<await menuButtons.count();i++) {
        const button=menuButtons.nth(i);if(!await button.isVisible())continue;
        await button.scrollIntoViewIfNeeded();
        const box=await button.boundingBox(),cd=await context.newCDPSession(page);
        await cd.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:box.x+box.width/2,y:box.y+box.height/2}]});
        const state=await button.evaluate(e=>{const s=getComputedStyle(e);return {type:e.dataset.buttonType,color:s.backgroundColor,opacity:s.opacity,filter:s.filter,held:e.matches(':active')||e.classList.contains('is-pressed')}});
        record(`Menu pressed ${await button.innerText()}`,width,state.held&&state.color===palette[state.type]&&state.opacity==='1'&&state.filter==='none',state);
        await cd.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await cd.detach();
      }
    }
    await page.goto(base+'/o-nas/');await page.evaluate(()=>document.fonts.ready);
    const hero=page.locator('.about-hero p');
    if(width===390) {
      const expected='Лучший сезон — это место, куда приезжают,\nчтобы побыть вместе.\nВстретить утро на террасе с кофе, днём уйти\nгулять по лесу, а вечером сесть у костра\nс гитарой или растопить баню.';
      record('About mobile hero copy and five lines',width,await hero.innerText()===expected&&near(await hero.evaluate(e=>e.getBoundingClientRect().height),85));
      const introLines=[
        ['Мы в Заокском районе Тульской области,','в двух часах от Москвы.','С трёх сторон лес, вдоль территории течёт','Скнижка, рядом питомник «Долина роз».'],
        ['Наш район считается одним из самых','чистых в области, воздух здесь чище','и плотнее — это заметно в первую','же ночь: спится здесь иначе.'],
        ['А ещё у нас есть собственная Ферма,','которая порадует свежими','и натуральными продуктами','к вашему завтраку.'],
      ];
      for(let i=0;i<3;i++) {
        const para=page.locator('.about-history__intro p').nth(i),actual=await para.evaluate(renderedLines);
        record(`About mobile intro lines #${i+1}`,width,JSON.stringify(actual)===JSON.stringify(introLines[i]),actual);
      }
      const storyLines=['Проект вырос из личной истории','и желания делиться.','В стенах нашего семейного дома','всегда было много друзей,','гостеприимства, длинных','разговоров и тёплых вечеров.','Со временем нас в семье','становилось всё больше — и тех,','с кем хотелось разделить','эту атмосферу и состояние, тоже.'];
      const story=page.locator('.about-history__row > p').first(),actual=await story.evaluate(renderedLines);
      record('About mobile story lines',width,JSON.stringify(actual)===JSON.stringify(storyLines),actual);
      record('About mobile story inset',width,await story.evaluate(e=>e.getBoundingClientRect().x)===120);
      await page.locator('.about-history__intro').screenshot({path:path.join(out,'about-intro-390.png')});
      await page.locator('.about-history__row').first().screenshot({path:path.join(out,'about-story-390.png')});
    }
    const cards=page.locator('.about-value');
    record('Six values',width,await cards.count()===6);
    // Raster glyph positions are taken from the supplied 400×600 reference.
    const positions=[[86,313,385],[173,274,318],[87,138,187],[209,260,332],[207,258,308],[216,270,318]];
    for(let i=0;i<await cards.count();i++) {
      const card=cards.nth(i);
      await card.evaluate(e=>{const track=e.closest('[data-about-track]');if(track.swiper)track.swiper.slideTo(Array.from(track.children).indexOf(e),0);e.querySelectorAll('img').forEach(img=>img.loading='eager')});
      await card.scrollIntoViewIfNeeded();await page.waitForTimeout(100);
      const png=PNG.sync.read(await card.screenshot({path:path.join(out,`value-${i+1}-${width}.png`)}));
      if(width===1440) {
        const parts=await card.evaluate(e=>{const card=e.getBoundingClientRect();return [...e.querySelectorAll('h3,.about-value__lead,.about-value__copy > p:last-child')].map(p=>{const b=p.getBoundingClientRect();return [Math.floor(b.top-card.top),Math.ceil(b.bottom-card.top),getComputedStyle(p).color]})});
        const measured=parts.map(([a,b,c])=>ink(png,c.match(/\d+/g).slice(0,3).map(Number),a,b));
        // Thin italic glyphs have no fully opaque pixels over a photograph.
        // An isolated black backing exposes their ink without changing metrics.
        const lead=card.locator('.about-value__lead');
        const oldStyle=await lead.getAttribute('style');
        await lead.evaluate(e=>{e.style.backgroundColor='#000';e.style.boxShadow='0 0 0 2px #000'});
        const leadPng=PNG.sync.read(await lead.screenshot());
        let firstRow=null;
        for(let y=0;y<leadPng.height&&firstRow===null;y++) {
          let count=0;
          for(let x=0;x<leadPng.width;x++){const k=(y*leadPng.width+x)*4;if(leadPng.data[k]>100&&leadPng.data[k+1]>80)count++;}
          if(count>=3)firstRow=y;
        }
        await lead.evaluate((e,old)=>old===null?e.removeAttribute('style'):e.setAttribute('style',old),oldStyle);
        measured[1]=firstRow===null?null:parts[1][0]+firstRow;
        record(`Value ${i+1} reference ink offsets`,width,measured.every((v,j)=>v!==null&&near(v,positions[i][j])),{measured,reference:positions[i],tolerance:2});
      } else record(`Value ${i+1} mobile containment`,width,await card.evaluate(e=>{const a=e.getBoundingClientRect(),b=e.querySelector('.about-value__copy').getBoundingClientRect();return b.bottom<=a.bottom+1&&a.height===525}));
    }
    record('Diary left alignment',width,(await page.locator('.about-entry h3').evaluateAll(es=>es.every(e=>getComputedStyle(e).textAlign==='left'))));
    await page.goto(base+'/razmeshchenie/domik-1/');
    await page.locator('[data-gallery-item]').first().click();
    const image=page.locator('[data-lightbox-image]');
    const first=await image.getAttribute('src');
    await page.locator('[data-lightbox-next]').click();
    record('Photo next',width,first!==await image.getAttribute('src'));
    await page.locator('[data-lightbox-prev]').click();
    record('Photo previous',width,first===await image.getAttribute('src'));
    await page.waitForTimeout(240);await page.mouse.move(0,0);
    for(const [side,wantX] of [['prev',19.7],['next',20.3]]) {
      const btn=page.locator(`[data-lightbox-${side}]`);
      const png=PNG.sync.read(await btn.screenshot({path:path.join(out,`arrow-${side}-${width}.png`)}));
      let total=0,xSum=0,ySum=0;
      for(let y=8;y<32;y++)for(let x=10;x<30;x++) {
        const k=(y*png.width+x)*4,color=Array.from(png.data.slice(k,k+3)),bg=[224,217,201],fg=[132,127,87];
        const weights=color.map((v,j)=>(bg[j]-v)/(bg[j]-fg[j]));
        const alpha=weights.reduce((a,b)=>a+b,0)/3;
        if(alpha>.01&&weights.every(w=>Math.abs(w-alpha)<.05)){total+=alpha;xSum+=(x+.5)*alpha;ySum+=(y+.5)*alpha;}
      }
      const center=[xSum/total,ySum/total];
      record(`Arrow ${side} optical centre`,width,total>0&&near(center[0],wantX,.6)&&near(center[1],20,.3),center);
    }
    if(width===390) {
      const box=await image.boundingBox(),cd=await context.newCDPSession(page);
      const x=box.x+box.width*.75,y=box.y+box.height*.5;
      await cd.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
      for(let step=1;step<=5;step++)await cd.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-step*20,y}]});
      await cd.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
      record('Photo real touch swipe',width,first!==await image.getAttribute('src'));await cd.detach();
    }
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.locator('[data-lightbox-next]').click();
    record('Photo reduced motion',width,await page.locator('[data-lightbox-next]').evaluate(e=>getComputedStyle(e).animationName==='none'));
    record('Content pageerror',width,errors.length===0,errors);
    await context.close();console.log('content and geometry',width,'checked');
  }
  for(const width of [320,360,412,430]) {
    const context=await browser.newContext({viewport:{width,height:900},deviceScaleFactor:1});
    await context.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
    const page=await context.newPage();
    for(const route of ['/','/razmeshchenie/','/akcii/','/o-nas/']) {
      await page.goto(base+route);await page.evaluate(()=>document.fonts.ready);
      record(`Overflow ${route}`,width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    }
    await context.close();
  }
};
