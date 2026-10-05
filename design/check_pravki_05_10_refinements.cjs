'use strict';
const navigate=require('./pravki_05_10_navigation.cjs');
const {PNG}=require('pngjs');
const fs=require('node:fs');
const path=require('node:path');
const reference=require('./pravki_05_10_lines.json');

function lines(e){
  const groups=new Map(),walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
    const node=walker.currentNode;
    for(let i=0;i<node.length;i++){
      const range=document.createRange();range.setStart(node,i);range.setEnd(node,i+1);
      const box=range.getBoundingClientRect();if(!box.width||!box.height)continue;
      const y=Math.round(box.y);groups.set(y,(groups.get(y)||'')+node.textContent[i]);
    }
  }
  return [...groups.values()].map(s=>s.trim().replace(/\s+/g,' ')).filter(Boolean);
}

module.exports=async function refinements(browser,base,out,checks){
  const record=(name,width,pass,detail)=>checks.push({name,width,pass,detail});
  for(const width of [1440,390]){
    const context=await browser.newContext({viewport:{width,height:1000},deviceScaleFactor:1,hasTouch:width===390,isMobile:width===390});
    await context.route('**/*',r=>new URL(r.request().url()).origin===base&&r.request().method()==='GET'?r.continue():r.abort());
    await context.addInitScript(()=>{
      try { localStorage.setItem('bs-cookie-consent-v1','dismissed'); } catch (_) {}
      document.addEventListener('click',e=>{if(e.target.closest('.btn,.searchbar--cta-only')){e.preventDefault();e.stopImmediatePropagation()}},true);
    });
    const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
    for(const route of ['/','/razmeshchenie/','/akcii/','/o-nas/']){
      await navigate(page,base+route);await page.evaluate(()=>document.fonts.ready);
      await page.evaluate(()=>document.querySelectorAll('.header').forEach(e=>e.style.visibility='hidden'));
      const buttons=page.locator('.searchbar--cta-only:visible,.btn.btn--outline:visible');
      for(let i=0;i<await buttons.count();i++){
        const button=buttons.nth(i);if(await button.isDisabled())continue;
        await button.scrollIntoViewIfNeeded();await page.mouse.move(0,0);await page.waitForTimeout(200);
        const shape=await button.evaluate(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {radius:parseFloat(s.borderTopLeftRadius),height:r.height,bg:s.backgroundColor,type:e.dataset.buttonType,wrapper:e.matches('.searchbar--cta-only')}});
        record(`Rounded button ${route} #${i+1}`,width,shape.radius>=shape.height/2-1,shape);
        if(!shape.wrapper&&shape.type!=='f')record(`Opaque outline default ${route} #${i+1}`,width,/^rgb\(/.test(shape.bg),shape);
        for(const state of ['hover','pressed']){
          if(width===390&&state==='hover')continue;
          let touch;
          if(width===390){const box=await button.boundingBox();touch=await context.newCDPSession(page);await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:box.x+box.width/2,y:box.y+box.height/2}]});}
          else {await button.hover();if(state==='pressed')await page.mouse.down();}
          await page.waitForTimeout(180);
          const bg=await button.evaluate(e=>getComputedStyle(e).backgroundColor),rgb=bg.match(/\d+/g)?.slice(0,3).map(Number);
          const png=PNG.sync.read(await button.screenshot());
          const corners=[[0,0],[png.width-1,0],[0,png.height-1],[png.width-1,png.height-1]];
          record(`Rounded ${state} ink ${route} #${i+1}`,width,!!rgb&&corners.every(([x,y])=>!rgb.every((v,j)=>Math.abs(png.data[(y*png.width+x)*4+j]-v)<2)),{background:bg});
          if(touch){await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await touch.detach();}
          else if(state==='pressed')await page.mouse.up();
        }
      }
      if(route!='/o-nas/'){
        await page.evaluate(()=>document.querySelectorAll('.faq__item').forEach(e=>{e.classList.add('is-open');e.querySelector('.faq__answer').hidden=false}));
        const answers=page.locator('.faq__answer');
        if(width===1440)for(let i=0;i<await answers.count();i++){
          const question=(await page.locator('.faq__question').nth(i).innerText()).replace(/\s+/g,' ').trim(),actual=await answers.nth(i).evaluate(lines);
          record(`FAQ reference lines ${route} #${i+1}`,width,JSON.stringify(actual)===JSON.stringify(reference[question]),actual);
        }
        await page.locator('.faq').screenshot({path:path.join(out,`refined-faq-${route==='/'?'home':route.split('/')[1]}-${width}.png`)});
      }
      if(route==='/o-nas/'){
        if(width===1440){
          const geometry=await page.locator('.about-history__intro').evaluate(e=>{const image=e.querySelector('.about-photo').getBoundingClientRect(),ps=[...e.querySelectorAll('p')].map(e=>e.getBoundingClientRect());return {gap:ps[0].x-image.right,paragraphGaps:[ps[1].top-ps[0].bottom,ps[2].top-ps[1].bottom]}});
          record('About desktop paragraph offsets',width,geometry.gap===30&&geometry.paragraphGaps.every(n=>n===24),geometry);
        }else{
          for(const [selector,expected]of [['.about-pets .about-section__lead',['Иногда к нам приходят котята, брошенные собаки','или кто-то ещё. Мы не приют — просто не умеем','проходить мимо. Пока для них не нашлись','хозяева, они живут у нас. Но если вы взглянете','на кого-то с этой страницы и поймёте, что это ваш,','— напишите нам.']],['.about-diary .about-section__lead',['Что у нас происходит: новые постройки, сезонные','затеи, наши рубрики и места по соседству, куда','стоит съездить.']]]){
            const actual=await page.locator(selector).evaluate(lines);record(`About reference lines ${selector}`,width,JSON.stringify(actual)===JSON.stringify(expected),actual);
          }
        }
        for(const [name,selector]of [['intro','.about-history__intro'],['pets','.about-pets'],['diary','.about-diary']])await page.locator(selector).screenshot({path:path.join(out,`refined-${name}-${width}.png`)});
      }
    }
    for(const narrow of width===390?[320,360,390,412,430]:[]){
      await page.setViewportSize({width:narrow,height:1000});await navigate(page,base+'/razmeshchenie/');
      const tiles=await page.locator('.mobile-service-tiles .service-tile').evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect();return {width:r.width,height:r.height}}));
      record('Mobile service tile proportions',narrow,tiles.length===4&&tiles.every(e=>Math.abs(e.width/e.height-170/179)<.005),tiles);
      await page.locator('.mobile-service-tiles .service-tile').first().click();
      record('Mobile tile opens without stretching',narrow,await page.locator('.mobile-service-tiles .service-tile').first().evaluate(e=>e.classList.contains('is-open')&&Math.abs(e.offsetWidth/e.offsetHeight-170/179)<.01));
      record('Mobile catalogue overflow',narrow,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    }
    record('Refinement page errors',width,errors.length===0,errors);await context.close();
  }
};
