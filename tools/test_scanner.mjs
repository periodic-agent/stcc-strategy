#!/usr/bin/env node
// test_scanner.mjs -- headless smoke test for card-browser-mockup.html.
//
// Why this exists: the scanner has an async init() path and inline onclick handlers that
// need their functions at GLOBAL scope. `node --check` passes on a file whose functions are
// all nested inside init(), yet every button in the browser is dead. This harness runs the
// real inline scripts in a DOM shim, then calls setView / clearAll / openLightbox from the
// same scope an inline handler would, so that class of bug fails here instead of in production.
//
// Usage:  node tools/test_scanner.mjs .            (from the repo root)
//         node tools/test_scanner.mjs . path/to/alternate.html
//
// Stdlib only, no deps. Exit code is non-zero on assertion failure.

import fs from 'fs';
import path from 'path';
import vm from 'vm';

// Minimal DOM shim: enough to run the scanner's scripts under node.

function makeEnv(repoDir){
  const listeners = {};
  function El(tag){
    return {
      tagName:tag, _cls:new Set(), dataset:{}, style:{}, children:[], attrs:{},
      _text:'', _html:'',
      set className(v){ this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
      get className(){ return [...this._cls].join(' '); },
      classList:{
        add:function(c){ this.__o._cls.add(c); },
        remove:function(c){ this.__o._cls.delete(c); },
        toggle:function(c,f){ const o=this.__o; const has=o._cls.has(c);
          const on = (f===undefined)? !has : !!f; if(on) o._cls.add(c); else o._cls.delete(c); return on; },
        contains:function(c){ return this.__o._cls.has(c); }
      },
      set textContent(v){ this._text=String(v); },
      get textContent(){ return this._text; },
      set innerHTML(v){ this._html=String(v); if(v==='') this.children=[]; },
      get innerHTML(){ return this._html; },
      set outerHTML(v){ this._outer=v; },
      appendChild(c){ this.children.push(c); return c; },
      append(...cs){ cs.forEach(c=>this.children.push(c)); },
      addEventListener(){}, scrollIntoView(){},
      setAttribute(k,v){ this.attrs[k]=v; }, getAttribute(k){ return this.attrs[k]; },
      querySelectorAll(sel){ return collect(this).filter(e=>matches(e,sel)); },
      querySelector(sel){ return this.querySelectorAll(sel)[0]||null; },
      click(){ if(this.onclick) this.onclick(); }
    };
  }
  function collect(root){
    const out=[]; (function walk(n){ n.children.forEach(c=>{ out.push(c); walk(c); }); })(root); return out;
  }
  function matches(el,sel){
    // supports ".cls", "span", ".a,.b", '.box-pill[data-box="x"]'
    return sel.split(',').map(s=>s.trim()).some(s=>{
      const m = s.match(/^([.\w-]+)?(\[data-(\w+)="([^"]+)"\])?$/);
      if(!m) return false;
      const base=m[1]||''; const dk=m[3]; const dv=m[4];
      if(base.startsWith('.')){ if(!el._cls.has(base.slice(1))) return false; }
      else if(base){ if(el.tagName!==base) return false; }
      if(dk && el.dataset[dk]!==dv) return false;
      return true;
    });
  }
  const registry = {};
  function ensure(id){
    if(!registry[id]){ const e=El('div'); e.id=id; e.classList.__o=e; registry[id]=e; }
    return registry[id];
  }
  const document = {
    _registry: registry,
    getElementById:(id)=>ensure(id),
    createElement:(t)=>{ const e=El(t); e.classList.__o=e; return e; },
    addEventListener:(t,f)=>{ (listeners[t]=listeners[t]||[]).push(f); },
    querySelectorAll:(sel)=>Object.values(registry).flatMap(r=>[r,...collect(r)]).filter(e=>matches(e,sel)),
    querySelector:(sel)=>document.querySelectorAll(sel)[0]||null,
    body:El('body')
  };
  document.body.classList.__o = document.body;
  const fetchLocal = async (f)=>{
    const p = path.join(repoDir, f);
    if(!fs.existsSync(p)) return {ok:false};
    return {ok:true, json: async ()=>JSON.parse(fs.readFileSync(p,'utf8'))};
  };
  return {document, fetch:fetchLocal, console, listeners};
}

function extractScripts(html){
  const out=[]; const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g; let m;
  while((m=re.exec(html))) out.push(m[1]);
  return out;
}


const repo = process.argv[2];
const file = process.argv[3] || (repo + '/cards.html');
const html = fs.readFileSync(file,'utf8');
const env = makeEnv(repo);
const sandbox = { ...env, window:{}, setTimeout, Set, Map, JSON, Math, Object, Array, String, Number };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

// All inline blocks share one global lexical scope in a browser; concatenate to match.
// The epilogue sits at that same scope, exactly like an inline onclick handler does,
// so anything it cannot see, a real button click cannot see either.
const body = extractScripts(html).join('\n;\n');
const epilogue = `
globalThis.__api = {
  get ALL_CARDS(){return ALL_CARDS;}, get activeBoxes(){return activeBoxes;},
  get viewMode(){return viewMode;}, get VISIBLE_IMG_CARDS(){return VISIBLE_IMG_CARDS;},
  render:()=>render(), cardMatches:(c)=>cardMatches(c), setView:(v)=>setView(v),
  clearAll:()=>clearAll(), showStrategy:(e)=>showStrategy(e), openLightbox:(s)=>openLightbox(s),
  stepLightbox:(d)=>stepLightbox(d),
  get STRATEGY_COUNTS(){return STRATEGY_COUNTS;}, get openStrategyId(){return openStrategyId;},
  buildPillCard:(c)=>buildPillCard(c), buildStrategyDrawer:(c)=>buildStrategyDrawer(c),
  ensureStrategyIndex:()=>ensureStrategyIndex(), toggleStrategy:(id)=>toggleStrategy(id)
};`;
vm.runInContext(body + '\n' + epilogue, sandbox, {filename:'scanner'});
await new Promise(r=>setTimeout(r,300));
const api = sandbox.__api;

function report(label){
  const shown = api.ALL_CARDS.filter(c=>api.cardMatches(c));
  const noimg = shown.filter(c=>!(c.imgBox && c.filename));
  console.log(`\n--- ${label} | boxes=[${[...api.activeBoxes]}] | resolved=${api.ALL_CARDS.length} shown=${shown.length} without image=${noimg.length}`);
  return {shown,noimg};
}

api.render();
report('default selection (three main boxes)');

api.setView('image');
console.log('setView("image") from global scope OK, viewMode =', api.viewMode);

api.activeBoxes.clear(); api.activeBoxes.add('tbg');
api.render();
const r = report('To Boldly Go ONLY, Images view');
const dupNoImg = r.noimg.filter(c=>c.badgeKind==='duplicate');
const updNoImg = r.noimg.filter(c=>c.badgeKind==='update');
console.log('duplicates with NO image:', dupNoImg.length, '|', dupNoImg.slice(0,6).map(c=>c.name).join(', '));
console.log('updated with NO image:', updNoImg.length, '|', updNoImg.map(c=>c.name).join(', '));

const vis = api.VISIBLE_IMG_CARDS;
const bad = vis.filter(e=>!fs.existsSync(repo+'/'+e.src));
console.log('lightbox entries:', vis.length, '| srcs missing on disk:', bad.length, bad.slice(0,4).map(b=>b.src));

// both boxes
api.activeBoxes.add('core'); api.render();
const r2 = report('Captain\'s Chair + To Boldly Go');
console.log('duplicates with NO image:', r2.noimg.filter(c=>c.badgeKind==='duplicate').length);

api.clearAll();
console.log('\nclearAll() from global scope OK');

// --- targeted assertions -----------------------------------------------------
function imgSrcFor(name, boxes){
  api.activeBoxes.clear(); boxes.forEach(b=>api.activeBoxes.add(b)); api.render();
  const c = api.ALL_CARDS.find(x=>x.name===name);
  if(!c) return 'CARD NOT IN SELECTION';
  return (c.imgBox && c.filename) ? ('img/'+({core:'box1',tbg:'box2','2nd':'box3',promo1:'promo1',promo2:'promo2'}[c.imgBox])+'/'+c.filename) : 'NO IMAGE';
}
console.log('\n=== image resolution checks ===');
for(const [n,b] of [['Rom',['tbg']],['Lursa',['tbg']],["V'Ger",['tbg']],['Phlox',['tbg']],['Phlox',['core']],['Phlox',['core','tbg']],['Solum',['tbg']],['Solum',['core']],['Tellarites',['tbg']]]){
  console.log(`${n} [${b}] -> ${imgSrcFor(n,b)}`);
}
api.activeBoxes.clear(); api.activeBoxes.add('tbg'); api.setView('image'); api.render();
const v2=api.VISIBLE_IMG_CARDS;
const missing=v2.filter(e=>!fs.statSync(repo+'/'+e.src,{throwIfNoEntry:false})?.isFile());
console.log('\nTBG-only Images: tiles with image =', v2.length, '| srcs not a real file:', missing.length, missing.slice(0,4).map(m=>m.src));
api.openLightbox('http://x/'+v2[0].src); api.stepLightbox(1); api.stepLightbox(-1);
console.log('lightbox open + arrow steps OK');

// --- hard assertions (non-zero exit on failure) ------------------------------
let failures = 0;
function assert(cond, label){
  if(cond){ console.log('  PASS  ' + label); }
  else { console.error('  FAIL  ' + label); failures++; }
}
console.log('\n=== assertions ===');
api.activeBoxes.clear(); api.activeBoxes.add('tbg'); api.setView('image'); api.render();
const tbgShown = api.ALL_CARDS.filter(c=>api.cardMatches(c));
assert(tbgShown.every(c=>!c.badgeKind || (c.imgBox && c.filename)),
  'Box 2 alone: no duplicate or update is left without an image');

// Current rule: a printing from a SELECTED box wins; printings from unselected boxes are
// fallback only. Among equals, the newest printing wins.
assert(imgSrcFor('Rom',['tbg']) === 'img/box2/rom.jpg',
  'a reprint browsed in Box 2 shows the Box 2 scan');
assert(imgSrcFor('Rom',['core']) === 'img/box1/rom.jpg',
  'the same reprint browsed in Box 1 shows the Box 1 scan');
assert(imgSrcFor('Rom',['core','tbg']) === 'img/box2/rom.jpg',
  'with both boxes selected the newest printing wins');
// Invariant, independent of which scans happen to exist: an updated card never inherits the
// art of the printing it superseded.
assert(imgSrcFor('Phlox',['tbg']) === 'img/box2/phlox.jpg',
  'updated Phlox uses its own Box 2 scan, never the superseded Box 1 art');
api.activeBoxes.clear(); ['core','tbg','2nd'].forEach(b=>api.activeBoxes.add(b)); api.render();
const updatedResolved = api.ALL_CARDS.filter(c=>c.variant === 'updated' && c.filename);
assert(updatedResolved.length > 0 && updatedResolved.every(c=>c.imgBox !== 'core'),
  'every updated card draws its image from the updated printing, not the original');

// Disk check runs only on a full checkout; a sparse or blobless clone has no img/ tree.
api.activeBoxes.clear(); api.activeBoxes.add('tbg'); api.setView('image'); api.render();
if(fs.existsSync(repo + '/img/box1')){
  assert(api.VISIBLE_IMG_CARDS.every(e=>fs.statSync(repo+'/'+e.src,{throwIfNoEntry:false})?.isFile()),
    'every lightbox entry points at a file that exists on disk');
} else {
  console.log('  SKIP  disk check: img/ not checked out in this clone');
}
assert(typeof api.setView === 'function' && typeof api.clearAll === 'function',
  'inline-handler functions are reachable at global scope');

// Box row: default selection and the "All" pill.
function freshBoxState(){
  api.activeBoxes.clear();
  ['core','tbg','2nd'].forEach(b=>api.activeBoxes.add(b));
  env.document.querySelectorAll('.box-pill').forEach(p=>{
    const id=p.dataset.box;
    if(id==='all') p.classList.remove('active');
    else p.classList.toggle('active', api.activeBoxes.has(id));
  });
  api.render();
}
const allPill = env.document.querySelector('.box-pill[data-box="all"]');
assert(!!allPill, 'the Box row carries an All pill');
assert(env.document.getElementById('boxFilters').children[0] === allPill,
  'the All pill is the first pill in the Box row');
freshBoxState();
assert([...api.activeBoxes].sort().join(',') === '2nd,core,tbg',
  'default selection is the three main boxes, promos off');
assert(!allPill.classList.contains('active'),
  'All pill is dim while only the default three are selected');
allPill.click();
assert([...api.activeBoxes].sort().join(',') === '2nd,core,promo1,promo2,tbg',
  'All selects every box including both promos');
assert(allPill.classList.contains('active'), 'All pill lights up once everything is selected');
allPill.click();
assert([...api.activeBoxes].sort().join(',') === '2nd,core,tbg',
  'a second All click returns to the three-box default');
assert(!allPill.classList.contains('active'), 'All pill dims again on the way back');
allPill.click();
env.document.querySelector('.box-pill[data-box="promo2"]').click();
assert(!allPill.classList.contains('active'),
  'deselecting any single box dims the All pill');
freshBoxState();

// Header banner: repointed at the strategy index.
api.setView('image');
api.showStrategy();
assert(api.viewMode === 'pill',
  'the header banner switches to Cards view, where the Strategy badge lives');
assert(/<span class="card-badge strategy">Strategy<\/span>[^<]*badge/.test(html),
  'the banner renders a real Strategy badge chip, not the word in plain text');
assert(/\.new-banner \.card-badge\{margin-bottom:0;\}/.test(html),
  'the inline badge drops the card-context bottom margin so the banner text stays centred');

// --- strategy index: badge, drawer, and link integrity ---------------------
// The drawer deep-links into guides, so a stale index would produce badges
// that lead to 404s or to anchors that no longer exist. Both are asserted
// here rather than discovered by a reader mid-game.

// Earlier assertions left the scanner filtered to Box 2 only; restore the
// full pool so these tests see every card.
api.activeBoxes.clear(); ['core','tbg','2nd'].forEach(b=>api.activeBoxes.add(b));
api.setView('pill'); api.render();

const counts = api.STRATEGY_COUNTS;
assert(Object.keys(counts).length > 0,
  'strategy-cards.json loaded and non-empty');

const discussed   = api.ALL_CARDS.find(c=>counts[c.id] !== undefined);
const undiscussed = api.ALL_CARDS.find(c=>counts[c.id] === undefined);

const pillYes = api.buildPillCard(discussed);
assert(pillYes.classList.contains('has-strategy')
       && pillYes.innerHTML.includes('card-badge strategy')
       && typeof pillYes.onclick === 'function',
  'a discussed card gets the Strategy badge and is clickable');

const pillNo = api.buildPillCard(undiscussed);
assert(!pillNo.classList.contains('has-strategy')
       && !pillNo.innerHTML.includes('card-badge strategy')
       && typeof pillNo.onclick !== 'function',
  'an undiscussed card gets no badge and no click target');

await api.ensureStrategyIndex();
const drawer = api.buildStrategyDrawer(discussed);
assert(drawer.className === 'strategy-drawer'
       && drawer.innerHTML.includes('sd-guide-title')
       && drawer.innerHTML.includes('Matthew McCue'),
  'the drawer renders guide links and carries the attribution line');

const idx = JSON.parse(fs.readFileSync(repo + '/data/strategy-index.json', 'utf8'));
const entries = Object.entries(idx.cards);

const missingGuides = [...new Set(entries.flatMap(([,es])=>es.map(e=>e.guide))
  .filter(g=>!fs.statSync(repo + '/' + g, {throwIfNoEntry:false})?.isFile()))];
assert(missingGuides.length === 0,
  'every guide referenced by the index exists on disk' + (missingGuides.length?' '+JSON.stringify(missingGuides):''));

const guideText = {};
const badAnchors = [];
for(const [cid, es] of entries){
  for(const e of es){
    for(const h of e.hits){
      if(!h.anchor) continue;
      guideText[e.guide] ??= fs.readFileSync(repo + '/' + e.guide, 'utf8');
      if(!guideText[e.guide].includes('id="' + h.anchor + '"')) badAnchors.push(cid + ' -> ' + e.guide + '#' + h.anchor);
    }
  }
}
assert(badAnchors.length === 0,
  'every drawer deep link points at an anchor that exists' + (badAnchors.length?' '+JSON.stringify(badAnchors.slice(0,5)):''));

// Compare against the raw card data, not the scanner's resolved pool, which
// is filtered by whatever boxes happen to be selected.
const knownIds = new Set(['box1.json','box2.json','box3.json']
  .filter(f=>fs.statSync(repo + '/' + f, {throwIfNoEntry:false})?.isFile())
  .flatMap(f=>JSON.parse(fs.readFileSync(repo + '/' + f, 'utf8')).map(c=>c.id)));
const orphanCards = Object.keys(idx.cards).filter(id=>!knownIds.has(id));
assert(orphanCards.length === 0,
  'every indexed card id still exists in the card data' + (orphanCards.length?' '+JSON.stringify(orphanCards.slice(0,5)):''));

console.log(failures ? `\n${failures} FAILURE(S)` : '\nAll assertions passed.');
process.exit(failures ? 1 : 0);
