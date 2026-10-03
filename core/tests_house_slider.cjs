const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('config/static/js/site.js','utf8');
const carousel=source.slice(source.indexOf('/* Фото карточек:'),source.indexOf('/* Карточки «Наша территория»'));
function setup(options={}){
  function el(){return {events:{},attrs:{},classList:{toggle(){}},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,f){this.events[k]=f;},blur(){this.blurred=true;},focus(){this.focused=true;}};}
  const slides=[el(),el(),el()],dots=[el(),el(),el()];
  let hovered=false,callback=null;
  const card={querySelectorAll:()=>dots,matches:()=>hovered,querySelector:()=>null,getBoundingClientRect:()=>({top:10,bottom:510})};
  const slider={...el(),children:slides,closest:()=>card,setPointerCapture(){}};
  const reduced={matches:!!options.reduced,addEventListener(){}};
  const doc={hidden:!!options.hidden,querySelectorAll:()=>[slider],addEventListener(){}};
  vm.runInNewContext(carousel,{document:doc,window:{innerHeight:1000,matchMedia:()=>reduced,clearTimeout(){callback=null;},setTimeout(f,ms){assert.equal(ms,3000);callback=f;return 1;}}});
  return {slider,dots,slides,reduced,doc,tick:()=>callback(), hasTimer:()=>!!callback,hover(v){hovered=v;},active:()=>dots.findIndex(d=>d.attrs['aria-selected']==='true')};
}
test('auto advances every 3 seconds, pauses on hover and respects reduced motion',()=>{
 const s=setup();assert.equal(s.active(),0);s.tick();assert.equal(s.active(),1);s.hover(true);s.tick();assert.equal(s.active(),1);
 assert.equal(setup({reduced:true}).hasTimer(),false);assert.equal(setup({hidden:true}).hasTimer(),false);
});
test('mouse changes photo; touch leaves the gesture to the outer cards; ordinary clicks navigate',()=>{
 for(const pointerType of ['mouse','touch']){
  const s=setup();const event=(x,y)=>({isPrimary:true,button:0,pointerId:1,pointerType,clientX:x,clientY:y});
  s.slider.events.pointerdown(event(200,100));s.slider.events.pointermove(event(100,100));s.slider.events.pointerup(event(100,100));
  assert.equal(s.active(),pointerType === 'mouse' ? 1 : 0);let prevented=false;s.slider.events.click({preventDefault(){prevented=true;}});assert.ok(prevented);
  prevented=false;s.slider.events.pointerdown(event(100,100));s.slider.events.pointerup(event(100,100));s.slider.events.click({preventDefault(){prevented=true;}});assert.equal(prevented,false);
 }
});
test('vertical touch scroll does not change photo and pointer cancellation resets drag',()=>{
 const s=setup();s.slider.events.pointerdown({isPrimary:true,button:0,pointerId:1,clientX:100,clientY:200});s.slider.events.pointerup({pointerId:1,clientX:105,clientY:100});assert.equal(s.active(),0);
 s.slider.events.pointerdown({isPrimary:true,button:0,pointerId:1,clientX:200,clientY:100});s.slider.events.pointercancel();s.tick();assert.equal(s.active(),1);
});
test('pointer dot click releases focus; keyboard arrows keep focus on selected dot and wrap',()=>{
 const s=setup();s.dots[2].events.click({detail:1,preventDefault(){}});assert.equal(s.active(),2);assert.ok(s.dots[2].blurred);
 s.dots[2].events.keydown({key:'ArrowRight',preventDefault(){}});assert.equal(s.active(),0);assert.ok(s.dots[0].focused);assert.equal(s.dots[0].tabIndex,0);assert.equal(s.dots[1].tabIndex,-1);
});
