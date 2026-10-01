const {test}=require('node:test');
const assert=require('node:assert/strict');
const create=require('../config/static/js/scroll-intent.js');

test('small trackpad movements do not change screen',()=>{
 const intent=create();for(let t=0;t<400;t+=80)assert.equal(intent.push(8,t),false);
});
test('confident accumulated movement within 400 ms changes screen',()=>{
 const intent=create();assert.equal(intent.push(40,0),false);assert.equal(intent.push(40,120),false);assert.equal(intent.push(40,250),true);
});
test('old deltas expire and reverse direction starts a new gesture',()=>{
 const intent=create();assert.equal(intent.push(100,0),false);assert.equal(intent.push(40,401),false);
 assert.equal(intent.push(-100,450),false);assert.equal(intent.push(-20,470),true);
});
test('inertia is ignored for 700 ms after a screen change',()=>{
 const intent=create();assert.equal(intent.push(120,0),true);assert.equal(intent.push(120,699),false);assert.equal(intent.push(120,700),true);
});
test('keyboard and touch transitions block wheel inertia as well',()=>{
 const intent=create();intent.block(200);assert.equal(intent.push(120,899),false);assert.equal(intent.push(120,900),true);
});
