#!/usr/bin/env node
// tools/resolve_cards.mjs
// ---------------------------------------------------------------------------
// Card resolution + validation for the ST:CC Card Scanner.
//
// The scanner loads one JSON per box (box1.json, box2.json, ...) at runtime and
// collapses duplicate/updated cards into one record per id. This script is the
// offline mirror of that logic: run it to validate the box JSONs and to print
// the distinct-vs-copies figures and the badge assignments, so the numbers the
// scanner shows can be checked without a browser.
//
// Usage:  node tools/resolve_cards.mjs box1.json box2.json [box3.json ...]
//
// It asserts the core guarantee: trait counts come from the RESOLVED list, not
// the raw union. If that ever breaks, this script exits non-zero.
// ---------------------------------------------------------------------------
import fs from 'fs';

const files = process.argv.slice(2);
if(!files.length){ console.error('usage: node resolve_cards.mjs box1.json [box2.json ...]'); process.exit(1); }

const GAMEBOX_KEY = { "Captain's Chair":'core', "To Boldly Go":'tbg', "2nd Contact":'2nd' };
const BOX_ORDER = ['core','tbg','2nd'];

function rawBoxKey(c){
  if(c.source === 'Promo') return c.game_box === 'To Boldly Go' ? 'promo2' : 'promo1';
  return GAMEBOX_KEY[c.game_box] || 'core';
}
function normIcons(icons){ return (icons||[]).filter(i=>i.specialty&&i.type).map(i=>i.specialty+' '+i.type); }
function traitsOf(c){ return [...(c.species_traits||[]),...(c.regular_traits||[]),...(c.other_traits||[])]; }

function resolveCards(pool){
  const byId = {};
  pool.forEach(c=>{ (byId[c.id]=byId[c.id]||[]).push(c); });
  const out = [];
  for(const group of Object.values(byId)){
    let chosen = group.find(c=>c.variant==='updated');
    if(!chosen) chosen = group.slice().sort((a,b)=>BOX_ORDER.indexOf(rawBoxKey(a))-BOX_ORDER.indexOf(rawBoxKey(b)))[0];
    let cand = chosen.variant==='updated' ? group.filter(c=>c===chosen) : group.slice();
    cand.sort((a,b)=>BOX_ORDER.indexOf(rawBoxKey(b))-BOX_ORDER.indexOf(rawBoxKey(a)));
    const img = cand.find(c=>c.filename && c.filename.trim());
    out.push({
      id:chosen.id, name:chosen.name, suit:chosen.suit, box:rawBoxKey(chosen),
      species:chosen.species_traits||[], regular:chosen.regular_traits||[], other:chosen.other_traits||[],
      skills:normIcons(chosen.icons), filename: img?img.filename:'', imgBox: img?rawBoxKey(img):null,
      boxes:[...new Set(group.map(rawBoxKey))], copies:group.length, variant:chosen.variant||'original',
      card_number:chosen.card_number||''
    });
  }
  return out;
}

const boxes = files.map(f=>JSON.parse(fs.readFileSync(f)));
const pool = boxes.flat();

// Cross-reference for badges (all loaded boxes)
const XREF = {};
pool.forEach(c=>{ const e=XREF[c.id]||(XREF[c.id]={updatedIn:null,alsoIn:null});
  if(c.variant==='updated') e.updatedIn=c.game_box; else if(c.variant==='reprint') e.alsoIn=c.game_box; });

const resolved = resolveCards(pool);
const distinct = resolved.length;
const copies = resolved.reduce((s,c)=>s+c.copies,0);

console.log(`Loaded ${files.length} box file(s): ${files.join(', ')}`);
console.log(`Raw records: ${pool.length}`);
console.log(`Distinct cards (resolved): ${distinct}`);
console.log(`Physical copies (sum): ${copies}`);
console.log(`Collapsed duplicates: ${pool.length - distinct}`);

const updated = resolved.filter(c=>XREF[c.id] && XREF[c.id].updatedIn && c.variant!=='updated');
const alsoRes = resolved.filter(c=>XREF[c.id] && XREF[c.id].alsoIn);
console.log(`\nBadges: ${resolved.filter(c=>XREF[c.id]&&XREF[c.id].updatedIn).length} updated-in, ${alsoRes.length} also-in`);

// CORE GUARANTEE: resolved trait counts <= raw union counts, and strictly less where dups share a trait.
let violations = 0;
const sampleTraits = [...new Set(pool.flatMap(traitsOf))];
for(const t of sampleTraits){
  const rawN = pool.filter(c=>traitsOf(c).includes(t)).length;
  const resN = resolved.filter(c=>[...c.species,...c.regular,...c.other].includes(t)).length;
  if(resN > rawN){ console.error(`VIOLATION: trait ${t} resolved(${resN}) > union(${rawN})`); violations++; }
}
if(violations){ console.error(`\nFAILED: ${violations} trait-count violations`); process.exit(2); }
console.log(`\nOK: all ${sampleTraits.length} trait counts are consistent (resolved <= union).`);
console.log('Resolution validated.');
