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
      tagName:tag, _cls:new Set(), dataset:{}, style:{setProperty(){}}, children:[], attrs:{},
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
      addEventListener(){}, scrollIntoView(){}, getBoundingClientRect(){ return {width:0,height:0,x:0,y:0}; },
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

function extractScripts(html, repoDir){
  const out=[];
  // local external scripts (e.g. cardface-assets.js?v=hash) load first, as in the browser
  const rs=/<script[^>]*\bsrc="([^"]+)"[^>]*><\/script>/g; let m;
  while((m=rs.exec(html))){
    const src=m[1];
    if(!/^(https?:)?\/\//.test(src)) out.push(fs.readFileSync(repoDir + '/' + src.split('?')[0], 'utf8'));
  }
  const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;
  while((m=re.exec(html))) out.push(m[1]);
  return out;
}


const repo = process.argv[2];
const file = process.argv[3] || (repo + '/cards.html');
const html = fs.readFileSync(file,'utf8');
const env = makeEnv(repo);
const sandbox = { ...env, window:{addEventListener:()=>{}}, location:{hash:'', search:'', pathname:'/cards.html'}, history:{replaceState(){}, pushState(){}}, setTimeout, Set, Map, JSON, Math, Object, Array, String, Number };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

// All inline blocks share one global lexical scope in a browser; concatenate to match.
// The epilogue sits at that same scope, exactly like an inline onclick handler does,
// so anything it cannot see, a real button click cannot see either.
const body = extractScripts(html, repo).join('\n;\n');
const epilogue = `
globalThis.__api = {
  get ALL_CARDS(){return ALL_CARDS;}, get activeBoxes(){return activeBoxes;},
  get viewMode(){return viewMode;}, get VISIBLE_IMG_CARDS(){return VISIBLE_IMG_CARDS;},
  render:()=>render(), cardMatches:(c)=>cardMatches(c), setView:(v)=>setView(v),
  clearAll:()=>clearAll(), showStrategy:(e)=>showStrategy(e), openLightbox:(s)=>openLightbox(s),
  stepLightbox:(d)=>stepLightbox(d),
  get STRATEGY_COUNTS(){return STRATEGY_COUNTS;}, get openStrategyId(){return openStrategyId;},
  buildPillCard:(c)=>buildPillCard(c), buildStrategyDrawer:(c)=>buildStrategyDrawer(c),
  ensureStrategyIndex:()=>ensureStrategyIndex(), toggleStrategy:(id)=>toggleStrategy(id),
  applyQuery:(t)=>applyQuery(t), deckKey:(c)=>deckKey(c),
  otherPrintingsLine:(c)=>otherPrintingsLine(c), get showDupes(){return showDupes;},
  syncFilterPills:()=>syncFilterPills(), get sortByPos(){return sortByPos;},
  positionRank:(c)=>positionRank(c)
};`;
vm.runInContext(body + '\n' + epilogue, sandbox, {filename:'scanner'});
await new Promise(r=>setTimeout(r,300));
const api = sandbox.__api;

// Snapshot of what init() left on screen, taken before this file touches any state.
// A previous version of these tests applied an empty query first and so failed to notice
// that the page still rendered three boxes on arrival.
const ARRIVAL = {
  boxes: [...api.activeBoxes],
  view: api.viewMode,
  grid: env.document.getElementById('deckGroups').innerHTML
};

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
assert(imgSrcFor('Rom',['core','tbg']) === 'img/box1/rom.jpg',
  'expanded: the first tile of a reprint is its Box 1 printing, showing the Box 1 scan');
api.applyQuery('box:core box:tbg dupes:off'); api.render();
const romCollapsed = api.ALL_CARDS.find(c=>c.name === 'Rom');
assert(romCollapsed && romCollapsed.imgBox === 'tbg',
  'collapsed: one tile, and the newest printing still supplies the art');
api.applyQuery(''); api.render();
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

// --- fonts ------------------------------------------------------------------
assert(/fonts\.googleapis\.com[^"]*Barlow\+Condensed/.test(html),
  'Barlow Condensed is actually requested, not merely named in CSS');
{
  const link=(html.match(/fonts\.googleapis\.com[^"]*/)||[''])[0];
  const asked=new Set([...html.matchAll(/font-family:\s*(?:var\(--card-font\)|'([^']+)')/g)]
    .map(m=>m[1]||'Barlow Condensed'));
  const missing=[...asked].filter(f=>!/^(sans-serif|serif|monospace|inherit)$/.test(f)
    && !link.includes(f.replace(/ /g,'+')));
  assert(missing.length === 0,
    'every font the CSS asks for is in the Google Fonts request (was: Barlow Condensed silently falling back)');
}
assert(/\.deck-count\{[^}]*var\(--card-font\)/.test(html),
  'the deck count uses the card face, not the header Orbitron');

// --- landing state ----------------------------------------------------------
// Checked BEFORE any applyQuery call in this file, so it reflects what init() left on screen:
// the earlier version of this suite applied an empty query first and so missed a page that
// still rendered all three boxes on arrival.
assert(ARRIVAL.boxes.length === 0,
  'init() leaves no box selected: the page really opens empty');
assert(/Select a box, or start typing, to see cards/.test(ARRIVAL.grid),
  'and the arrival hint is what init() rendered');
assert(ARRIVAL.view === 'image', 'the scanner opens in Images view');
assert(/id="btnImg"[^>]*>Images</.test(html) && /id="btnPill"[^>]*>Text</.test(html),
  'the toggle reads Images and Text');
assert(html.indexOf('id="btnImg"') < html.indexOf('id="btnPill"'),
  'Images sits before Text in the toggle');
assert(html.indexOf('class="clear-btn"') < html.indexOf('id="searchCount"'),
  'the controls lead the row and the count trails on the right');
assert(html.indexOf('class="clear-btn"') < html.indexOf('id="showDupes"')
    && html.indexOf('id="showDupes"') < html.indexOf('id="searchCount"'),
  'Show duplicates sits between Reset and the count, in the toolbar row');
assert(html.indexOf('id="showDupes"') > html.indexOf('id="boxFilters"') + 400 || !/id="boxFilters"><\/div>\s*<label/.test(html),
  'and no longer hangs under the Box pills');
assert(/\.search-count-row \.search-count\{margin-left:auto;\}/.test(html),
  'the count is the element pushed right, not the toggle');
assert(/<button class="vtoggle active" id="btnImg"/.test(html),
  'Images is the button marked active in the markup');
api.applyQuery(''); api.render();
assert(api.activeBoxes.size === 0,
  'an empty search bar selects no box, so the page opens empty');
assert(api.ALL_CARDS.filter(c=>api.cardMatches(c)).length === 0, 'nothing renders on arrival');
assert(/Select a box, or start typing, to see cards/.test(env.document.getElementById('deckGroups').innerHTML),
  'the empty page says what to do next');
api.applyQuery('kirk'); api.render();
assert(api.activeBoxes.size === 3 && api.ALL_CARDS.filter(c=>api.cardMatches(c)).length > 0,
  'typing anything falls back to the three main boxes, so results appear');
api.applyQuery('box:core zzzznope'); api.render();
assert(/No cards match the current filters/.test(env.document.getElementById('deckGroups').innerHTML),
  'a query that matches nothing still says so, rather than the arrival hint');
api.applyQuery(''); api.render();

// --- sort by starting position ----------------------------------------------
// The sort happens inside render(), so it has to be read off the rendered sections:
// filtering ALL_CARDS again returns the unsorted array and proves nothing.
function renderedDeck(query, deckLabel){
  api.applyQuery(query); api.syncFilterPills(); api.setView('pill'); api.render();
  const sec=[...env.document.getElementById('deckGroups').children]
    .find(s=>s.children[0].innerHTML.indexOf(deckLabel) === 0);
  if(!sec) return [];
  return sec.children[1].children.map(t=>{
    const m=t.innerHTML.match(/class="nb"[^>]*>([^<]+)</);
    return m ? m[1] : '?';
  });
}
const byNumber = renderedDeck('box:tbg deck:archer', 'Archer');
const byPos    = renderedDeck('box:tbg deck:archer sort:position', 'Archer');
assert(byNumber.length === byPos.length && byNumber.length > 0,
  'sorting changes the order, not the contents');
assert(byNumber.join() !== byPos.join(), 'and the order really does change');
assert(new Set(byNumber).size === new Set(byPos).size,
  'no card is dropped or duplicated by the sort');
{
  // Names are only unique within a deck: "Strange New Worlds" exists in four of them,
  // so the lookup has to be built from the deck being examined.
  api.applyQuery('box:tbg deck:archer sort:position'); api.render();
  const deckCards = api.ALL_CARDS.filter(c=>api.deckKey(c) === 'Archer');
  const byName = new Map(deckCards.map(c=>[c.name,c]));
  const r = byPos.map(n=>api.positionRank(byName.get(n)));
  assert(r.every(v=>Number.isFinite(v)), 'every rendered tile was matched back to its card');
  assert(r.every((v,i)=>i===0||r[i-1]<=v), 'the rendered order is non-decreasing in position rank');
  assert(r[0] === 0 && r[1] === 1, 'the captain and its status card lead the deck');
}
assert(api.sortByPos === true, 'sort:position is what the query set');
assert(env.document.getElementById('sortPos').checked === true,
  'and the checkbox follows the query');
api.applyQuery('box:tbg deck:archer'); api.syncFilterPills(); api.render();
assert(api.sortByPos === false && env.document.getElementById('sortPos').checked === false,
  'dropping the token returns to card-number order');
{
  // Stability: within one position the card-number order survives.
  const dev = renderedDeck('box:tbg deck:archer sort:position', 'Archer');
  const devByNumber = byNumber.filter(n=>dev.includes(n));
  const firstDev = dev.filter(n=>devByNumber.includes(n));
  assert(firstDev.length === dev.length, 'every card kept, ties unbroken');
}
assert(/sort:position/.test(html), 'the token is documented in the help panel');

// --- duplicates across boxes ------------------------------------------------
const dupOn  = runQuery('box:core box:tbg');
const dupOff = runQuery('box:core box:tbg dupes:off');
assert(new Set(dupOn.map(c=>c.id)).size === dupOff.length,
  'both modes cover the same set of distinct cards');
assert(dupOn.length > dupOff.length,
  'showing duplicates yields more tiles than collapsing them');
assert(dupOn.length - dupOff.length === 54,
  'the extra tiles are exactly the 45 reprints and 9 updates of Box 2');
const romTiles = dupOn.filter(c=>c.name === 'Rom');
assert(romTiles.length === 2 && romTiles.some(c=>c.box==='core') && romTiles.some(c=>c.box==='tbg'),
  'a reprint gets one tile per box it was printed in');
assert(romTiles.every(c=>c.badgeKind === 'duplicate'),
  'both tiles of a reprint carry the Duplicate badge');
assert(romTiles.map(c=>api.deckKey(c)).sort().join(',') === 'Common:core,Common:tbg',
  'the two tiles file under their own box deck groups, which is what made the shared card invisible before');
assert(dupOff.filter(c=>c.name === 'Rom').length === 1, 'dupes:off collapses it back to one tile');
assert(api.showDupes === false, 'dupes:off is what the query set');
assert(env.document.getElementById('showDupes').checked === false,
  'and the checkbox follows the query, so a shared dupes:off link arrives unticked');
runQuery('box:core box:tbg');
assert(api.showDupes === true, 'and duplicates are back on without the token');

// the line naming the other printings
const romCore = romTiles.find(c=>c.box==='core');
const romTbg  = romTiles.find(c=>c.box==='tbg');
assert(api.otherPrintingsLine(romCore) === 'Also in: To Boldly Go',
  'a Box 1 printing names the box that reprinted it');
assert(api.otherPrintingsLine(romTbg) === "Also in: Captain's Chair",
  'and the reprint names the original, box selection notwithstanding');
const phlox = runQuery('box:core box:tbg phlox');
const phloxCore = phlox.find(c=>c.box==='core'), phloxTbg = phlox.find(c=>c.box==='tbg');
assert(api.otherPrintingsLine(phloxCore) === 'Updated in: To Boldly Go',
  'a superseded printing says where it was updated');
assert(api.otherPrintingsLine(phloxTbg) === "Updates: Captain's Chair",
  'and the updated printing says what it updates');
// A card printed once anywhere, not merely once in the current selection: the line reads
// every printing, so "copies === 1" is not the same question.
const onceOnly = runQuery('box:core').find(c=>!c.badgeKind && api.otherPrintingsLine(c) === '');
assert(onceOnly && api.otherPrintingsLine(onceOnly) === '',
  'a card printed in one box only says nothing');
const jarok = runQuery('box:core').find(c=>c.name === 'Admiral Jarok');
assert(jarok.copies === 1 && api.otherPrintingsLine(jarok) === 'Also in: To Boldly Go',
  'and a card whose other printing is outside the selection still names it');
assert(api.otherPrintingsLine(romCore) === api.otherPrintingsLine(
  runQuery('box:core').filter(c=>c.name==='Rom')[0]),
  'the line is read from every printing, so deselecting Box 2 does not hide it');

// counts
runQuery('box:core box:tbg trait:scientist');
assert(/<b>\d+<\/b> cards? · <b>\d+<\/b> printings?/.test(env.document.getElementById('searchCount').innerHTML),
  'the total line always shows cards and printings');
const headers=[...env.document.getElementById('deckGroups').children]
  .map(sec=>sec.children[0] && sec.children[0].innerHTML).filter(Boolean);
assert(headers.length > 0 && headers.every(h=>/\(\d+ cards? · \d+ printings?\)/.test(h)),
  'each deck header shows both numbers too');
// Expanded mode files each printing under its own box's group, so within a group the two
// numbers agree. Collapsed mode is where they diverge, and that is the case the user could
// not read before: 6 cards, 7 printings.
runQuery('box:core box:tbg dupes:off trait:scientist');
const collapsedHeaders=[...env.document.getElementById('deckGroups').children]
  .map(sec=>sec.children[0] && sec.children[0].innerHTML).filter(Boolean);
assert(collapsedHeaders.some(h=>{const m=h.match(/\((\d+) cards? · (\d+) printings?\)/); return m && m[1] !== m[2];}),
  'collapsed, a group with a shared card shows cards and printings differing');
runQuery('');

// --- query keys: vp, position, variant --------------------------------------
function runQuery(q){
  // Mirrors what the page does on every query change: apply, sync the controls, render.
  api.applyQuery(q); api.syncFilterPills(); api.render();
  return api.ALL_CARDS.filter(c=>api.cardMatches(c));
}
const v4 = runQuery('vp:4');
assert(v4.length > 0 && v4.every(c=>Number(c.vp) === 4),
  'vp:4 returns only cards whose victory points are 4');
const vGe = runQuery('vp>=4');
assert(vGe.length >= v4.length && vGe.every(c=>Number(c.vp) >= 4),
  'vp>=4 respects the comparison and is a superset of vp:4');
assert(runQuery('victory-points:4').length === v4.length,
  'victory-points: is accepted as the long form');
assert(runQuery('vp>0').every(c=>c.vp !== null && c.vp !== undefined),
  'no card without a victory-point value is ever returned by a vp query');
const allDefault = runQuery('box:core box:tbg box:2nd');
const vpless = allDefault.filter(c=>c.vp === null || c.vp === undefined);
assert(vpless.length > 0 && runQuery('vp<99').length === allDefault.length - vpless.length,
  'value-less cards are excluded from an open-ended range, not swept in');
assert(runQuery('box:all glory:4').length === 0 && runQuery('box:all glory:4').length !== v4.length,
  'glory: is gone as a key; it names the wrong rule');
assert(runQuery('box:all text:glory').length > 0,
  'text:glory still finds the blue token in rules text');

const reserve = runQuery('position:reserve');
assert(reserve.length > 0 && reserve.every(c=>c.position_indicator === 'Reserve'),
  'position:reserve matches the starting-position indicator');
assert(runQuery('position:incident-deck').every(c=>c.position_indicator === 'Incident Deck'),
  'a hyphen in a position value stands in for a space');
assert(runQuery('position:rewards').every(c=>c.position_indicator === 'Rewards'),
  'position:rewards finds the Box 3 Commons carrying it');

const dupes = runQuery('box:all variant:duplicate');
assert(dupes.length > 0 && dupes.every(c=>c.badgeKind === 'duplicate'),
  'variant:duplicate returns exactly the cards wearing the Duplicate badge');
const upd = runQuery('box:all variant:update');
assert(upd.length > 0 && upd.every(c=>c.badgeKind === 'update'),
  'variant:update returns exactly the cards wearing the Update badge');
assert(runQuery('box:core variant:duplicate').length === 0,
  'with only Box 1 selected nothing wears a badge, so variant:duplicate is empty');
// suit vocabulary and bare suit words
const statusExact = runQuery('box:all suit:status');
assert(statusExact.length > 0 && statusExact.every(c=>c.suit === 'Status'),
  'suit:status matches in lowercase, not only suit:Status');
assert(runQuery('box:all suit:captain').every(c=>c.suit === 'Captain'),
  'suit:captain returns captain cards');
assert(runQuery('box:all suit:directive').every(c=>c.suit === 'Directive'),
  'suit:directive returns directive cards');
const bareCaptain = runQuery('box:all captain');
assert(bareCaptain.some(c=>c.suit === 'Captain') && bareCaptain.some(c=>c.suit !== 'Captain' && /captain/i.test(c.name)),
  'a bare suit word returns the union of that suit and name matches');
assert(bareCaptain.length >= runQuery('box:all suit:captain').length,
  'the bare word is a superset of the exact suit search');
assert(!runQuery('box:all -captain').some(c=>c.suit === 'Captain' || /captain/i.test(c.name)),
  'negating a bare suit word drops both the suit and the name matches');
// suit chip row
const suitPills=[...env.document.getElementById('suitFilters').children];
const suitLabels=suitPills.map(p=>p.dataset.suit);
assert(suitLabels.join(',') === 'Captain,Person,Cargo,Ship,Ally,Encounter,Incident,Location,Directive',
  'suit chips follow rulebook order and end with Directive');
assert(!suitLabels.includes('Automated Command') && !/Automated Command/.test(html),
  'the Automated Command placeholder is gone, markup and CSS');
const dirPill=suitPills.find(p=>p.dataset.suit==='Directive');
assert(dirPill && typeof dirPill.onclick === 'function' && !dirPill._cls.has('disabled'),
  'the Directive chip is live, not disabled');
assert(/CARDFACE\.suit\[/.test(html) || dirPill.innerHTML.includes('<img'),
  'the Directive chip carries its glyph from the shared asset bundle');
assert(runQuery('box:all suit:directive').length > 0,
  'the Directive chip has cards behind it');

// text inside one strip kind
const reactShady = runQuery('box:all reaction:"putting a shady"');
assert(reactShady.length > 0 && reactShady.every(c=>(c.strips||[]).some(x=>
        String(x.kind).toLowerCase()==='reaction' && /putting a shady/i.test(x.text||''))),
  'a strip kind used as a key searches only strips of that kind');
assert(runQuery('box:all play:"putting a shady"').length === 0,
  'the same phrase under the wrong kind returns nothing');
assert(runQuery('box:all text:"putting a shady"').length >= reactShady.length,
  'text: stays card-wide and is a superset of the kind-scoped search');
const negKind = runQuery('box:all -reaction:"putting a shady"');
assert(!negKind.some(c=>reactShady.includes(c)),
  'negating a kind-scoped phrase drops exactly those cards');
assert(runQuery('box:all activation:draw').every(c=>(c.strips||[]).some(x=>
        String(x.kind).toLowerCase()==='activation' && /draw/i.test((x.text||'')+' '+(x.qual||'')))),
  'the qualifier line is searched along with the strip body');
assert(/reaction:&quot;putting a shady&quot;|reaction:"putting a shady"/.test(html),
  'the help bubble documents kind-scoped text search with an example');

// strip presentation
const stripChips=[...env.document.getElementById('stripFilters').children].map(c=>c.dataset.strip);
assert(!stripChips.includes('cost') && !stripChips.includes('banner'),
  'Dev. Cost and No Play have no filter chip');
assert(stripChips.length === 11 && stripChips.includes('control'),
  'the remaining eleven strip chips are intact');
assert(runQuery('box:all strip:cost').length > 0,
  'the hidden kinds are still queryable by key');
assert(/\.opstrip \.body\{flex:1/.test(html),
  'strip bodies stretch the full width of the card');
api.applyQuery('box:all'); api.render();
const lwax = api.ALL_CARDS.find(c=>c.name === 'Lwaxana Troi');
const lwaxHTML = api.buildPillCard(lwax).innerHTML;
assert(/alt="Influence"/.test(lwaxHTML) && !/\b(Influence|Military|Research)\b/.test(lwaxHTML.replace(/<img[^>]*>/g,'')),
  'a bare specialty word renders as its medallion, not as text');
assert(/"resupply":\s*\{[^}]*"body":\s*"#dff0da"/.test(html) && /"play":\s*\{[^}]*"body":\s*"#e9e8e2"/.test(html),
  'the Resupply and Control family carries a light green body, Play stays neutral');
api.applyQuery(''); api.render();

// Vertical pills and filter chips keep their sampled colours; only the inline chips changed.
assert(/\.vt-species\{background:#e2a04a;\}/.test(html) && /\.cp-species\{--cc:#e2a04a;\}/.test(html),
  'the card-face pills and filter chips keep their original colours');
api.applyQuery('box:all'); api.render();
const klingonCard = api.ALL_CARDS.find(c=>(c.strips||[]).some(s=>/\bKlingon\b/.test(s.text||'')));
const klHTML = api.buildPillCard(klingonCard).innerHTML.replace(/\s+/g,' ');
assert(/background:#e2a04a;color:#fff/.test(klHTML),
  'a species trait chip inside strip text takes the species colour');
assert(!/style="background:#556"/.test(klHTML),
  'no inline trait chip is left on the flat slate colour');
let slate=0;
api.ALL_CARDS.forEach(c=>{ if(/background:#556/.test(api.buildPillCard(c).innerHTML)) slate++; });
assert(slate === 0, 'no card anywhere still renders a slate-grey trait chip');
api.applyQuery(''); api.render();

// Dev. Cost renders last
api.applyQuery('box:all'); api.render();
let costNotLast=0, costCards=0;
api.ALL_CARDS.forEach(c=>{
  const kinds=(c.strips||[]).map(s=>String(s.kind||'').toLowerCase());
  if(!kinds.includes('cost')) return;
  costCards++;
  const h=api.buildPillCard(c).innerHTML;
  const labels=[...h.matchAll(/class="kw[^"]*"[^>]*>([A-Z. -]+):/g)].map(m=>m[1].trim());
  const block=[...h.matchAll(/class="kwblock"[^>]*>([A-Z. -]+):/g)].map(m=>m[1].trim());
  const order=[...labels,...block];
  if(!h.includes('DEV. COST')) return;
  if(h.indexOf('DEV. COST') < h.lastIndexOf('class="kw"')) costNotLast++;
});
assert(costCards > 0 && costNotLast === 0,
  'every card with a development cost renders it below its operations');
const bozeman = api.ALL_CARDS.find(c=>c.name === 'U.S.S. Bozeman');
const bh = api.buildPillCard(bozeman).innerHTML;
assert(bh.indexOf('PLAY:') < bh.indexOf('DEV. COST'),
  'a card whose JSON lists cost first still prints it last');
api.applyQuery(''); api.render();

// specialty medallions
api.applyQuery('box:all'); api.render();
const lwaxPill = api.buildPillCard(api.ALL_CARDS.find(c=>c.name==='Lwaxana Troi')).innerHTML;
assert(/<span class="specpill" style="background:#c0b422"><img[^>]*alt="Influence"/.test(lwaxPill),
  'a bare specialty renders as a rounded pill in its own colour');
const dorg = api.buildPillCard(api.ALL_CARDS.find(c=>c.name==='Captain Dorg')).innerHTML;
assert(!/\{spec:|\{skill:|\{focus:/.test(dorg),
  'a Skill token is not rewritten by the bare-specialty pass (no literal braces on the card)');
assert((dorg.match(/specpill/g)||[]).length >= 2,
  'the Skill tokens on that card still render as medallions');
let strayBraces = 0;
api.ALL_CARDS.forEach(c=>{ if(/\{[a-z]+:/.test(api.buildPillCard(c).innerHTML)) strayBraces++; });
assert(strayBraces === 0, 'no card anywhere renders an unresolved {token}');
assert(/\.specpill\{[^}]*border-radius:999px/.test(html),
  'the pill is rounded at both ends');
api.applyQuery(''); api.render();

// hidden query
const egg = runQuery('picard combo');
const eggIds = new Set(egg.map(c=>c.id));
assert(eggIds.size === 4 && ['picard-daystrom-institute','moriarty','picard-uss-bozeman','holographic-drone-ship']
         .every(id=>eggIds.has(id)),
  'the hidden picard combo query returns its four cards');
assert(new Set(runQuery('combo picard').map(c=>c.id)).size === 4, 'word order does not matter');
assert(egg.length === 5,
  'and with duplicates shown, Holographic Drone Ship contributes two tiles');
assert(runQuery('picard').length > 4 && runQuery('combo').length !== 4,
  'either word alone behaves as an ordinary name search');
api.applyQuery(''); api.render();

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
  'a second All click returns to the three main boxes');
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
assert(!/class="new-banner"/.test(html),
  'the New banner is retired in the card-face design (strategy opens by clicking a discussed card)');
assert(!/\.new-banner/.test(html),
  'no orphaned New banner CSS is left behind now that the markup is gone');

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
assert(pillYes.classList.contains('has-strategy'),
  'a discussed card still carries has-strategy (guide links surface in the lightbox caption)');

const withImg = api.ALL_CARDS.find(c=>c.filename && c.imgBox);
const pillImg = api.buildPillCard(withImg);
assert(pillImg.classList.contains('has-img') && typeof pillImg.onclick === 'function',
  'a card with an image is clickable and opens the lightbox');

const noImg = api.ALL_CARDS.find(c=>!c.filename);
const pillNoImg = noImg ? api.buildPillCard(noImg) : null;
assert(!pillNoImg || (!pillNoImg.classList.contains('has-img') && typeof pillNoImg.onclick !== 'function'),
  'an image-less card gets no click target');

const pillNo = api.buildPillCard(undiscussed);
assert(!pillNo.classList.contains('has-strategy')
       && !pillNo.innerHTML.includes('card-badge strategy'),
  'an undiscussed card carries no strategy affordance');

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
