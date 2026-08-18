#!/usr/bin/env python3
"""Add operation strips to the Card Scanner: a STRIP filter category, the
strip: and text: query tokens, and the strips themselves on the card faces.

cards.html is the repo's source of truth and several chats edit it directly, so
this applies targeted edits to whatever the file currently contains rather than
regenerating it. Every anchor is asserted, so an upstream refactor fails loudly
here instead of silently dropping a change, and the script is idempotent.

The strip data is not in the box JSONs yet. Everything below is written against
the agreed shape and lies dormant until it lands: chips read (0), no strip
renders, nothing breaks. That is the same way the glory badge shipped.

    "strips": [{"kind": "play", "action": true, "qual": "Action",
                "text": "Discard a card with Research Skill ..."}]

The text is verbatim crowd transcription with no token markup, so icons are
matched from the words at render time. Suits and traits keep their word because
the card prints a chip carrying both; resources and the action token replace it
because the card prints art alone.

Usage: python3 patch_strips.py <cards.html> <strip_palette.json> [out.html]
"""
import sys, json

# One chip per kind, coloured by family. The families are visual; the kinds are
# not (ACTIVATION, PASSIVE and REACTION have different timing rules), so each
# stays independently filterable.
KINDS = [
    ('play', 'Play'), ('support', 'Support'),
    ('resupply', 'Resupply'), ('cleanup', 'Clean-Up'), ('control', 'Control'),
    ('activation', 'Activation'), ('reaction', 'Reaction'), ('passive', 'Passive'),
    ('special', 'Special'), ('surprise', 'Surprise'),
    ('endgame', 'Endgame'), ('cost', 'Dev. Cost'), ('banner', 'No Play'),
]
# kind -> palette entry supplying its colours
FAMILY = {'play': 'play', 'support': 'play', 'control': 'resupply',
          'resupply': 'resupply', 'cleanup': 'cleanup',
          'activation': 'activation', 'reaction': 'activation', 'passive': 'activation',
          'special': 'special', 'surprise': 'surprise',
          'endgame': 'endgame', 'cost': 'cost', 'banner': 'banner'}


def patch(s, palette):
    if 'STRIP_PALETTE' in s:
        print('already patched; nothing to do')
        return s

    # ---- 1. data: palette, kind list, family map ----
    anchor = "let QUERY_VOCAB=null;"
    assert anchor in s, 'QUERY_VOCAB anchor'
    s = s.replace(anchor,
        "const STRIP_PALETTE=" + json.dumps(palette) + ";\n"
        "const STRIP_KINDS=" + json.dumps(KINDS) + ";\n"
        "const STRIP_FAMILY=" + json.dumps(FAMILY) + ";\n"
        "let activeStrips=new Set(), negStrips=new Set(), textTerms=[], negText=[];\n\n"
        + anchor, 1)

    # ---- 2. parser: strip: and text: ----
    old = """    } else if(key==='variant'){"""
    assert old in s, 'parser variant branch'
    s = s.replace(old,
        """    } else if(key==='strip'){
      // strip:reaction, and strip:any for "has any strip at all"
      put(res.strips,res.negStrips,lv.replace(/[\\s-]/g,''));
    } else if(key==='text'||key==='rules'){
      // free text across every strip on the card: this is what makes the rules
      // searchable rather than merely filterable
      put(res.text,res.negText,lv);
    } else if(key==='variant'){""", 1)

    old = "glory:[],negGlory:[],positions:[],negPositions:[],variants:[],negVariants:[]};"
    assert old in s, 'parser result shape'
    s = s.replace(old, "glory:[],negGlory:[],positions:[],negPositions:[],variants:[],negVariants:[],\n"
                       "             strips:[],negStrips:[],text:[],negText:[]};", 1)

    old = "  activeVariants=new Set(q.variants);   negVariants=new Set(q.negVariants);"
    assert old in s, 'applyQuery tail'
    s = s.replace(old, old + "\n  activeStrips=new Set(q.strips); negStrips=new Set(q.negStrips);\n"
                             "  textTerms=q.text; negText=q.negText;", 1)

    # ---- 3. matching ----
    old = "  const pos=c.position_indicator;"
    assert old in s, 'cardMatches position anchor'
    s = s.replace(old,
        "  // Strips: kind filter, then free text over the concatenated strip text.\n"
        "  const kinds=(c.strips||[]).map(x=>String(x.kind||'').toLowerCase());\n"
        "  if(activeStrips.size && ![...activeStrips].every(k=>k==='any'?kinds.length:kinds.includes(k))) return false;\n"
        "  if([...negStrips].some(k=>k==='any'?kinds.length:kinds.includes(k))) return false;\n"
        "  if(textTerms.length||negText.length){\n"
        "    const blob=(c.strips||[]).map(x=>x.text||'').join(' ').toLowerCase();\n"
        "    if(textTerms.length && !textTerms.every(t=>blob.includes(t))) return false;\n"
        "    if(negText.some(t=>blob.includes(t))) return false;\n"
        "  }\n"
        + old, 1)

    # ---- 4. resolver passthrough ----
    old = "      away_team: (() => { for (const pr of group) { if (pr.away_team) return String(pr.away_team); } return ''; })(),"
    assert old in s, 'resolver away_team anchor'
    s = s.replace(old, old + "\n      strips: (() => { for (const pr of group) { if (Array.isArray(pr.strips) && pr.strips.length) return pr.strips; } return []; })(),", 1)

    # ---- 5. the filter section, directly under Focus ----
    old = """    <div class="collapsible-body open" id="focusBody">
      <div class="pill-row" id="focusFilters"></div>
    </div>
  </div>
"""
    assert old in s, 'focus section'
    s = s.replace(old, old + """
  <div class="filter-group">
    <div class="collapsible-header open" onclick="toggleSection(this,'stripBody','stripSummary')">
      <div style="display:flex;align-items:center;gap:0.4rem;">
        <div class="filter-label">Strip</div>
        <span class="active-summary skill" id="stripSummary"></span>
      </div>
      <span class="collapsible-arrow">&#9660;</span>
    </div>
    <div class="collapsible-body open" id="stripBody">
      <div class="pill-row" id="stripFilters"></div>
      <div class="strip-note">Counts reflect transcribed cards only; text is still being added.</div>
    </div>
  </div>
""", 1)

    # ---- 6. chip construction ----
    old = "document.getElementById('speciesFilters').append("
    assert old in s, 'pill append anchor'
    s = s.replace(old, """const stripContainer=document.getElementById('stripFilters');
STRIP_KINDS.forEach(([kind,label])=>{
  const pal=STRIP_PALETTE[STRIP_FAMILY[kind]]||{};
  const p=document.createElement('span');
  p.className='strip-pill cardpill'; p.dataset.strip=kind;
  p.style.setProperty('--cc', pal.bar||'#8494ad');
  p.innerHTML='<span class="lbl">'+label+'</span><span class="cnt"></span>';
  p.onclick=()=>toggleToken(tokenOf('strip',kind));
  stripContainer.appendChild(p);
});

""" + old, 1)

    # ---- 7. counts and active state ----
    old = "  updatePillCounts('focusFilters',allSkills.filter(v=>/Focus$/.test(v)),true);"
    assert old in s, 'updatePillCounts tail'
    s = s.replace(old, old + """
  // Strip chips count per kind against the cards currently matching everything else.
  document.querySelectorAll('#stripFilters > span').forEach(p=>{
    const kind=p.dataset.strip;
    let n=0;
    ALL_CARDS.forEach(c=>{ if((c.strips||[]).some(x=>String(x.kind||'').toLowerCase()===kind)) n++; });
    const cnt=p.querySelector('.cnt');
    cnt.textContent='('+n+')';
    if(!cnt.style.minWidth) cnt.style.minWidth=Math.ceil(cnt.getBoundingClientRect().width)+'px';
    p.classList.toggle('active', activeStrips.has(kind));
    p.classList.toggle('zero', n===0);
  });""", 1)

    # ---- 8. rendering on the card face ----
    old = "  const badge=badgeInfo(c);"
    assert old in s, 'buildPillCard badge anchor'
    s = s.replace(old, "  const stripHTML=buildStrips(c);\n" + old, 1)

    old = "    +numline+corner;"
    assert old in s, 'card innerHTML tail'
    s = s.replace(old, "    +stripHTML+numline+corner;", 1)

    old = "function buildPillCard(c){"
    assert old in s, 'buildPillCard'
    s = s.replace(old, STRIP_JS + "\n" + old, 1)

    # ---- 9. styling ----
    old = '</style>'
    assert old in s, 'style close'
    s = s.replace(old, STRIP_CSS + "</style>", 1)

    # ---- 10. asset cache-buster ----
    # The bundle gains the token art in this same change, so the ?v= hash has to
    # move or the CDN keeps serving the old one and every icon silently vanishes.
    import hashlib, os, re as _re
    if os.path.exists('cardface-assets.js'):
        ver = hashlib.md5(open('cardface-assets.js', 'rb').read()).hexdigest()[:8]
        s2 = _re.sub(r'cardface-assets\.js\?v=[a-f0-9]+', 'cardface-assets.js?v=' + ver, s)
        assert s2 != s or ver in s, 'asset version not found'
        s = s2
        print('asset cache-buster ->', ver)

    # ---- 10. help popover ----
    old = """    <div class="qh-row"><code>variant:update</code>"""
    assert old in s, 'help popover anchor'
    s = s.replace(old,
        """    <div class="qh-row"><code>strip:reaction</code> &middot; <code>strip:any</code>"""
        """<span>cards carrying that operation strip</span></div>\n"""
        """    <div class="qh-row"><code>text:cloak</code> &middot; <code>text:"gain 2"</code>"""
        """<span>search the rules text of every strip</span></div>\n""" + old, 1)
    return s


STRIP_CSS = """
/* ===== operation strips =====
   Colours are sampled from the card scans and white-point corrected per card;
   the correction target is solved so ENDGAME reproduces the values already
   shipped on archer-scoring.html. See tools/extract_strip_colors.py. */
.ce-strips{margin:.45rem -0.7rem .1rem;display:flex;flex-direction:column;gap:2px;}
.opstrip{display:flex;border-radius:0 4px 4px 0;overflow:hidden;}
.opstrip .bar{flex:none;width:3px;}
.opstrip .body{padding:.2rem .45rem .22rem .4rem;font-family:'Barlow Condensed',sans-serif;
  font-weight:500;font-size:.8rem;line-height:1.24;}
.opstrip .kw{font-family:'Antonio',sans-serif;font-weight:600;letter-spacing:.02em;
  font-size:.76rem;text-shadow:0 0 2px #fff,0 0 5px rgba(255,255,255,.85);}
.opstrip.on-dark .kw{text-shadow:0 0 2px rgba(10,20,40,.9);}
.opstrip .line + .line{margin-top:.1rem;}
/* DEV. COST is the one strip whose keyword sits inside the dark block, which
   sizes itself to the text rather than being a fixed bar. */
.opstrip.inbar .kwblock{flex:none;display:flex;align-items:center;padding:.2rem .4rem .22rem;
  font-family:'Antonio',sans-serif;font-weight:600;font-size:.76rem;letter-spacing:.02em;}
.stripimg{height:1.35em;width:auto;vertical-align:-.32em;margin:0 .08em;}
.stripimg.cost{margin:0 .22em 0 0;}
.stripchip{display:inline-flex;align-items:center;gap:.18em;height:1.2em;padding:0 .38em 0 .1em;
  border-radius:999px;font-family:'Antonio',sans-serif;font-weight:600;font-size:.85em;
  letter-spacing:.03em;text-transform:uppercase;color:#fff;vertical-align:-.2em;}
.stripchip img{height:1em;width:auto;}
.stripchip.plain{padding-left:.38em;}
.strip-pill{padding-left:.5rem;}
.strip-pill.zero{opacity:.45;}
.strip-note{font-family:'Exo 2',sans-serif;font-size:.62rem;color:var(--muted);
  margin:.35rem 0 0;opacity:.85;}
"""

STRIP_JS = r"""// ===== operation strips on the card face =====
// The transcription is plain text: nobody recorded which words were printed as
// chips or icons, so they are matched here. Suits and traits keep their word,
// because the card prints a chip carrying both the mark and the word; resources
// and the action token replace it, because the card prints art alone.
const STRIP_SUIT_COL={Person:'#c9ab35',Ally:'#9b6ecf',Ship:'#7a8aaa',Cargo:'#3a6aaa',
  Location:'#4ac48a',Encounter:'#d4699f',Incident:'#e05a5a',Captain:'#c8a84b',
  Directive:'#8494ad',Status:'#88aacc',Mission:'#2b3040'};
const STRIP_RES={dilithium:'dilithium',latinum:'latinum',glory:'glory-token',
                 action:'action',actions:'action'};
const STRIP_SPEC=['Research','Influence','Military','Any','Variable'];

function stripIcon(key){
  // CARDFACE is a top-level const, so it is not a property of window: guard
  // with typeof, not window.CARDFACE, which is always undefined here.
  return (typeof CARDFACE!=='undefined' && CARDFACE.token && CARDFACE.token[key])||'';
}
function titleCase(w){ return w.charAt(0).toUpperCase()+w.slice(1); }

function stripToken(t){
  let m;
  if((m=t.match(/^suit:(.+)$/))){
    const s=m[1], col=STRIP_SUIT_COL[s]||'#8494ad';
    const gi=(CARDFACE.suitFont&&CARDFACE.suitFont[s.toLowerCase()])||CARDFACE.suit[s.toLowerCase()];
    return '<span class="stripchip'+(gi?'':' plain')+'" style="background:'+col+'">'
      +(gi?'<img src="'+gi+'" alt="">':'')+s.toUpperCase()+'</span>';
  }
  if((m=t.match(/^trait:(.+)$/))){
    const k=m[1].toLowerCase().replace(/['\u2019]/g,'').replace(/\s+/g,'-');
    const ic=CARDFACE.traitChip[k];
    return '<span class="stripchip'+(ic?'':' plain')+'" style="background:#556">'
      +(ic?'<img src="'+ic+'" alt="">':'')+m[1].toUpperCase()+'</span>';
  }
  if((m=t.match(/^(skill|focus):(.+)$/))){
    const bank=m[1]==='focus'?CARDFACE.focus:CARDFACE.skillChip;
    const src=bank&&bank[m[2].toLowerCase()];
    return src?'<img class="stripimg" src="'+src+'" alt="'+m[2]+'">':m[2]+' '+m[1];
  }
  if((m=t.match(/^res:(.+)$/))){
    const src=stripIcon(STRIP_RES[m[1].toLowerCase()]);
    return src?'<img class="stripimg" src="'+src+'" alt="'+m[1]+'">':titleCase(m[1]);
  }
  if(t==='action'){
    const src=stripIcon('action');
    return src?'<img class="stripimg" src="'+src+'" alt="action">':'action';
  }
  return t;
}

function stripAutoTokens(text){
  let t=text;
  STRIP_SPEC.forEach(sp=>{
    t=t.replace(new RegExp('\\b'+sp+' (Skill|Focus)\\b','g'),
      (_,k)=>'{'+(k==='Focus'?'focus':'skill')+':'+sp+'}');
  });
  Object.keys(STRIP_SUIT_COL).forEach(w=>{
    t=t.replace(new RegExp('\\b'+w+'s?\\b','g'),()=>'{suit:'+w+'}');
  });
  Object.keys(STRIP_RES).forEach(w=>{
    t=t.replace(new RegExp('\\b'+w+'\\b','gi'),
      m=>/^(dilithium|latinum|glory)$/i.test(m)?'{res:'+m.toLowerCase()+'}':'{action}');
  });
  // Traits only where a medallion exists and only capitalised, so an ordinary
  // "attack" in a sentence stays text while the ATTACK trait becomes a chip.
  Object.keys(CARDFACE.traitChip).forEach(k=>{
    t=t.replace(new RegExp('\\b'+k.replace(/-/g,' ')+'\\b','gi'),
      m=>(m[0]===m[0].toUpperCase()?'{trait:'+m+'}':m));
  });
  return t;
}

function stripBody(text){
  return stripAutoTokens(String(text||''))
    .replace(/\{([^}]+)\}/g,(_,t)=>stripToken(t))
    .replace(/_([^_]+)_/g,'<em>$1</em>');
}

function stripLabel(kind){
  return ({cleanup:'CLEAN-UP',cost:'DEV. COST'}[kind])||kind.toUpperCase();
}

// Consecutive strips of the same colour family share one box, which is how the
// cards print them (PLAY with SUPPORT, REACTION with PASSIVE).
function buildStrips(c){
  const list=c.strips||[];
  if(!list.length) return '';
  const boxes=[];
  list.forEach(st=>{
    const fam=STRIP_FAMILY[String(st.kind||'').toLowerCase()]||'play';
    const last=boxes[boxes.length-1];
    if(last && last.fam===fam) last.items.push(st); else boxes.push({fam:fam,items:[st]});
  });
  return '<div class="ce-strips">'+boxes.map(b=>{
    const p=STRIP_PALETTE[b.fam]; if(!p) return '';
    const ink=p.text==='light'?'#f2f6ff':'#14161c';
    const dark=p.text==='light'?' on-dark':'';
    if(p.mode==='inbar'){
      return '<div class="opstrip inbar'+dark+'">'+b.items.map(st=>
          '<div class="kwblock" style="background:'+p.bar+';color:'+(p.keyword||'#fff')+'">'
          +stripLabel(String(st.kind).toLowerCase())+':</div>'
        + '<div class="body" style="background:'+p.body+';color:'+ink+'">'
          +stripBody(st.text)+'</div>').join('')+'</div>';
    }
    return '<div class="opstrip'+dark+'"><div class="bar" style="background:'+p.bar+'"></div>'
      +'<div class="body" style="background:'+p.body+';color:'+ink+'">'
      + b.items.map(st=>{
          const cost=st.action===true?('<img class="stripimg cost" src="'+stripIcon('action')+'" alt="action cost">'):'';
          const kind=String(st.kind||'').toLowerCase();
          return '<div class="line">'+cost
            +(kind==='banner'?'':'<span class="kw" style="color:'+(p.keyword||ink)+'">'+stripLabel(kind)+':</span> ')
            +stripBody(st.text)+'</div>';
        }).join('')
      +'</div></div>';
  }).join('')+'</div>';
}

"""


def main(src, palette_json, out=None):
    s = open(src).read()
    pal = json.load(open(palette_json))
    open(out or src, 'w').write(patch(s, pal))
    print('wrote', out or src)


if __name__ == '__main__':
    main(*sys.argv[1:])
