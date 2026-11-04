const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {initTagSearch, matchingTags, resultUrl} = require('../app/webpage/tag-search.js');
class Element {
  constructor(tag='div') {this.tag=tag; this.children=[]; this.events={}; this.dataset={}; this.attrs={}; this.value=''; this.hidden=true;}
  addEventListener(type,fn) {(this.events[type] ||= []).push(fn);}
  fire(type,event={}) {for(const fn of this.events[type] || []) fn({preventDefault(){},...event});}
  append(child) {this.children.push(child);}
  replaceChildren() {this.children=[];}
  setAttribute(key,value) {this.attrs[key]=value;}
  querySelector(selector) {
    if(selector==='[data-tag-input]') return this.input;
    if(selector==='[data-tag-options]') return this.panel;
    if(selector==='button') return this.children.find(child=>child.tag==='button');
  }
  contains(target) {return target===this || target===this.input || target===this.panel || this.panel?.children.includes(target);}
  focus() {this.fire('focus');}
}
async function scenario(fail=false) {
  const container = new Element(); container.input=new Element('input'); container.panel=new Element();
  const document = new Element(); document.querySelectorAll=()=>[container]; document.createElement=tag=>new Element(tag);
  global.document=document; global.location={href:''};
  let fetches=0;
  global.shopApi=path=>path+'?userType=vendor&vendorID=V1';
  global.fetch=async url=>{fetches++; assert(url.includes('vendorID=V1')); return {ok:!fail,json:async()=>({success:true,tags:['Books & Art','Electronics']})};};
  initTagSearch(); initTagSearch();
  container.input.fire('focus');
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(fetches,1);
  if(fail) {
    assert(container.panel.children[0].textContent.includes('Unable to load'));
    assert.equal(global.location.href,'');
    return;
  }
  assert.equal(container.panel.children.length,2);
  container.input.value='book'; container.input.fire('input');
  assert.equal(container.panel.children.length,1);
  assert.equal(container.panel.children[0].textContent,'Books & Art');
  // Clicking a dropdown tag must navigate immediately, with no second button.
  container.panel.children[0].fire('click');
  assert.equal(global.location.href,'search_tag.html?tag=Books%20%26%20Art');
  assert.equal(container.panel.hidden,true);
  global.location.href=''; container.input.value='electronics';
  container.input.fire('keydown',{key:'Enter'});
  assert.equal(global.location.href,'search_tag.html?tag=Electronics');
  global.location.href=''; container.input.value='missing'; container.input.fire('input');
  assert.equal(container.panel.children[0].textContent,'No matching tags.');
  container.input.fire('keydown',{key:'Enter'});
  assert.equal(global.location.href,'');
}
(async()=>{
  assert.deepEqual(matchingTags(['Books','Electronics'],'BOOK'),['Books']);
  assert.equal(resultUrl('a+b'),'search_tag.html?tag=a%2Bb');
  await scenario(); await scenario(true);
  const folder=path.resolve(__dirname,'../app/webpage');
  let pages=0;
  for(const name of fs.readdirSync(folder).filter(name=>name.endsWith('.html'))) {
    const html=fs.readFileSync(path.join(folder,name),'utf8');
    assert(!/<button\b[^>]*>\s*Search\s*<\/button>/i.test(html),name);
    assert(!html.includes("searchButton.addEventListener"),name);
    if(html.includes('data-tag-search')) {pages++; assert(html.includes('src="tag-search.js"'),name);}
  }
  assert.equal(pages,9);
  console.log('PASS: immediate tag selection, URL encoding, input filtering, Enter, empty/error states, idempotent initialization, and 9 button-free search bars');
})().catch(error=>{console.error(error);process.exitCode=1;});
