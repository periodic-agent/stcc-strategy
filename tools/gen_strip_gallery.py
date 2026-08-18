#!/usr/bin/env python3
"""Build the operation-strip component gallery.

Renders every operation strip at full size and at card-tile size, each beside
the scan crop it was derived from, so the match can be judged by eye. The strip
renderer and the inline-token parser here are the ones intended to move into
cards.html once the JSON carries operation text, so they are written as plain
JS against the existing CARDFACE asset bundle.

Usage: python3 gen_strip_gallery.py <palette.json> <crop_dir> <assets.js> <out.html>
"""
import sys, json, base64, os

# Measured values, with two deliberate overrides:
#   endgame  - the shipped #eecac7/#e03511 win over the resample (which lands
#              within 4 per channel); the live page is the reference.
#   keyword ink and text polarity on the blue boxes - sampling returns the box
#              colour there because the ink is white; the cards plainly show
#              white keyword and white body text, so those are set, per the
#              instruction not to derive polarity from a formula.
OVERRIDE = {
    'endgame':    {'bar': '#e03511', 'body': '#eecac7', 'keyword': '#e03511', 'text': 'dark'},
    'resupply':   {'text': 'dark'},
    'cleanup':    {'text': 'dark'},
    'special':    {'text': 'dark'},
    'banner':     {'text': 'dark', 'keyword': '#c24b36'},
    'play':       {'text': 'dark', 'keyword': '#14161c'},
    'table':      {'text': 'light', 'keyword': '#ffffff'},
    'passive':    {'text': 'light', 'keyword': '#ffffff'},
    'activation': {'text': 'light', 'keyword': '#ffffff'},
}

# Transcribed from the four reference scans. Inline tokens use the proposed
# JSON contract: {glory:N} {suit:Ship} {trait:Klingon} {skill:Influence}
# {focus:Research} {action} {res:blue} {chip:Mission}, with _underscores_ for
# the italics the cards use on card names and on rules emphasis.
SAMPLES = {
    'resupply': [('RESUPPLY', 'If you have a deployed {suit:Ship} and 3+ resources at _Earth_, '
                              'you _may_ exhaust this card to gain 3 resources from _Earth_.')],
    'endgame': [('ENDGAME', 'Score {glory:1} for every 3 unique traits you have in play.')],
    'cleanup': [('CLEAN-UP', 'You _may_ beam a non-{suit:Directive} card here from your hand or '
                             'Staging Area. If it shares no traits with your {suit:Captain}, '
                             'gain 1 {skill:Influence} and place 1 {res:glory} here.')],
    'table': [('REACTION', 'After discarding a {suit:Directive} during your Action Step, '
                           'place 1 {res:dilithium} / {res:latinum} here.'),
              ('PASSIVE', '{suit:Ship} can warp here. Cards beamed here cannot be recalled or '
                          'dismissed, not even when contributing to a {chip:Mission}.')],
    'banner': [(None, 'THIS CARD CANNOT BE PLAYED.')],
    'passive': [('PASSIVE', 'While this card is in play, treat it as though it were exhausted.')],
    'special': [('SPECIAL', 'Before scoring, find and return up to 2 {suit:Incident}.')],
    'play': [('PLAY', 'Spend all your remaining {action} (possibly none). For each {action} spent '
                      'this way, draw a card; then draw one additional card. Free play one of the '
                      'drawn cards.'),
             ('SUPPORT', 'After promoting a {suit:Person}, duplicate a play operation of that card.')],
    'activation': [('ACTIVATION', 'Discard a card with {skill:Research} and take an '
                                  '{suit:Incident} to enlist a Development.', True)],
    'cost': [('DEV. COST', '{res:dilithium} x2, and take an {suit:Incident}.')],
    'surprise': [('SURPRISE', '(Bot only): Gain 1 {res:glory} and discard the top card of the '
                              'Bot deck. You gain 2 {res:dilithium}. Return this card.')],
}

ORDER = ['play', 'resupply', 'cleanup', 'table', 'activation', 'passive',
         'special', 'surprise', 'endgame', 'cost', 'banner']


def datauri(path):
    # crops go in as JPEG: they are photographs of print, and PNG made the
    # gallery four times larger for no visible gain
    from PIL import Image
    import io
    im = Image.open(path).convert('RGB')
    if im.width > 900:
        im = im.resize((900, max(1, round(im.height * 900 / im.width))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=86)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def main(palette_json, crop_dir, assets_js, out, rbicons_js='rulebook-icons.js'):
    pal = json.load(open(palette_json))
    for k, ov in OVERRIDE.items():
        if k in pal:
            pal[k].update(ov)
    assets = open(assets_js).read() + '\n' + open(rbicons_js).read()
    crops = {k: datauri(os.path.join(crop_dir, k + '.png'))
             for k in pal if os.path.exists(os.path.join(crop_dir, k + '.png'))}

    data = {'palette': pal, 'samples': {k: [list(x) for x in v] for k, v in SAMPLES.items()},
            'order': ORDER, 'crops': crops}

    html = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Operation strips</title>
<link href="https://fonts.googleapis.com/css2?family=Antonio:wght@600&family=Barlow+Condensed:wght@400;500;600&family=Orbitron:wght@600;700&family=Exo+2:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#0d1119;--panel:#141a25;--text:#e8ecf5;--muted:#8a94ac;}
body{margin:0;background:var(--bg);color:var(--text);font-family:'Exo 2',sans-serif;}
main{max-width:1180px;margin:0 auto;padding:2rem 1.5rem 4rem;}
h1{font-family:'Orbitron',sans-serif;font-size:1.15rem;letter-spacing:.08em;}
p.lede{color:var(--muted);font-size:.9rem;max-width:70ch;line-height:1.5;}
h2{font-family:'Orbitron',sans-serif;font-size:.82rem;letter-spacing:.1em;color:#6fd3d3;
   margin:2.4rem 0 .6rem;border-top:1px solid rgba(120,140,180,.22);padding-top:1.1rem;}
.crop img{width:100%;max-width:760px;display:block;border-radius:4px;
   box-shadow:0 2px 12px rgba(0,0,0,.5);}
.cap{color:var(--muted);font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;margin:.9rem 0 .35rem;}
.sw{display:flex;gap:.5rem;flex-wrap:wrap;margin:.4rem 0 .2rem;}
.sw span{font-family:'Exo 2',sans-serif;font-size:.68rem;color:var(--muted);
   display:flex;align-items:center;gap:.35rem;}
.sw i{width:15px;height:15px;border-radius:3px;display:inline-block;
   box-shadow:inset 0 0 0 1px rgba(255,255,255,.25);}
/* ---------- the component ---------- */
.opstrip{display:flex;max-width:760px;border-radius:0 7px 7px 0;overflow:hidden;margin:.3rem 0;}
.opstrip .bar{flex:none;width:6px;}
/* DEV. COST: keyword lives in the dark block itself, which sizes to the text */
.opstrip.inbar .kwblock{flex:none;display:flex;align-items:center;padding:.5rem .8rem .55rem;
  font-family:'Antonio',sans-serif;font-weight:600;letter-spacing:.02em;font-size:1.15rem;}
.opstrip.mini.inbar .kwblock{padding:.18rem .4rem .2rem;font-size:.76rem;}
.opstrip .body{padding:.5rem .9rem .55rem;font-family:'Barlow Condensed',sans-serif;
   font-weight:500;font-size:1.15rem;line-height:1.32;}
.opstrip .kw{font-family:'Antonio',sans-serif;font-weight:600;letter-spacing:.02em;
   text-shadow:0 0 2px #fff,0 0 5px rgba(255,255,255,.9);}
.opstrip.on-dark .kw{text-shadow:0 0 2px rgba(10,20,40,.9),0 0 6px rgba(10,20,40,.7);}
.opstrip .line + .line{margin-top:.18rem;}
/* card-tile size: the halo smears below about 1rem, so it is weakened here */
.opstrip.mini{max-width:248px;border-radius:0 3px 3px 0;margin:.16rem 0;}
.opstrip.mini .bar{width:3px;}
.opstrip.mini .body{padding:.18rem .45rem .2rem .4rem;font-size:.8rem;line-height:1.22;}
.opstrip.mini .kw{font-size:.76rem;text-shadow:0 0 2px #fff,0 0 5px rgba(255,255,255,.85);}
.opstrip.mini.on-dark .kw{text-shadow:0 0 2px rgba(10,20,40,.9);}
/* ---------- inline tokens ---------- */
.tok{display:inline-flex;align-items:center;gap:.2em;height:1.24em;padding:0 .42em 0 .12em;
   border-radius:999px;font-family:'Antonio',sans-serif;font-weight:600;font-size:.86em;
   letter-spacing:.03em;text-transform:uppercase;color:#fff;vertical-align:-.22em;}
.tok img{height:1.05em;width:auto;}
.tok.plain{padding-left:.42em;}
.glory-inline{height:1.3em;width:auto;vertical-align:-.3em;margin:0 .06em;}
.skill-inline{height:1.15em;width:auto;vertical-align:-.24em;margin:0 .08em;border-radius:2px;}
.tokimg{height:1.45em;width:auto;vertical-align:-.36em;margin:0 .1em;}
.tokimg.act{height:1.35em;vertical-align:-.3em;}
.tokimg.cost{margin-right:.25em;margin-left:0;}
.gap{display:inline-flex;align-items:center;height:1.2em;padding:0 .4em;border-radius:3px;
   border:1px dashed #d08a5a;color:#e0a070;font-family:'Exo 2',sans-serif;font-size:.72em;
   letter-spacing:.04em;vertical-align:-.16em;background:rgba(208,138,90,.12);}
.tilebox{background:#101622;border:1px solid rgba(120,140,180,.25);border-radius:10px;
   padding:.6rem;width:266px;}
.cols{display:flex;gap:1.6rem;flex-wrap:wrap;align-items:flex-start;}
footer{color:var(--muted);font-size:.75rem;text-align:center;padding:2rem 0 0;}
</style></head><body><main>
<h1>OPERATION STRIPS</h1>
<p class="lede">Every operation rendered at full size and at card-tile size, each under the scan
crop it was sampled from. Colours are white-point corrected per card; the correction target is
solved so that Archer's ENDGAME reproduces the values already shipped on archer-scoring.html,
and every other box uses the identical transform. Orange dashed boxes mark tokens whose artwork
is drawn from the rulebook back cover: resource and action tokens by path
transcription, suit and Mission marks from the embedded icon font.</p>
<div id="out"></div>
<footer>Card images &copy; WizKids.</footer>
</main>
<script>__ASSETS__</script>
<script>
const D = __DATA__;

const SUIT_COL={Person:'#c9ab35',Ally:'#9b6ecf',Ship:'#7a8aaa',Cargo:'#3a6aaa',
  Location:'#4ac48a',Encounter:'#d4699f',Incident:'#e05a5a',Captain:'#c8a84b',
  Directive:'#8494ad',Status:'#88aacc'};

// Inline token vocabulary. Anything unknown renders as a visible gap marker
// rather than silently disappearing.
function token(t){
  let m;
  if((m=t.match(/^glory:(-?\\d+|\\?)$/))){
    const v=m[1], warm=v.startsWith('-');
    return '<svg class="glory-inline" viewBox="0 0 32 29" role="img" aria-label="Glory '+v+'">'
      +'<ellipse cx="16" cy="14.5" rx="15.5" ry="11" fill="#fff"/>'
      +'<path transform="translate(16 14.5) scale(1.7) translate(-13 -11.65)" d="M13 3.6c2.3 4 5.2 10.2 7.5 16.1-2.7-2-5.1-2.9-7.5-2.9s-4.8.9-7.5 2.9C7.8 13.8 10.7 7.6 13 3.6z" fill="'
      +(warm?'#f0a893':'#c3cfdd')+'"/><text x="16" y="21.7" text-anchor="middle" font-size="20" '
      +'font-weight="700" fill="#10161f" font-family="Antonio,sans-serif">'+v+'</text></svg>';
  }
  if((m=t.match(/^suit:(.+)$/))){
    const s=m[1], col=SUIT_COL[s]||'#8494ad';
    const gi=(RBICON.suit[s.toLowerCase()]||CARDFACE.suit[s.toLowerCase()]);
    return '<span class="tok'+(gi?'':' plain')+'" style="background:'+col+'">'
      +(gi?'<img src="'+gi+'" alt="">':'')+s.toUpperCase()+'</span>';
  }
  if((m=t.match(/^trait:(.+)$/))){
    const k=m[1].toLowerCase().replace(/['\\u2019]/g,'').replace(/\\s+/g,'-');
    const ic=CARDFACE.traitChip[k];
    return '<span class="tok'+(ic?'':' plain')+'" style="background:#556">'
      +(ic?'<img src="'+ic+'" alt="">':'')+m[1].toUpperCase()+'</span>';
  }
  if((m=t.match(/^(skill|focus):(.+)$/))){
    const bank=m[1]==='focus'?CARDFACE.focus:CARDFACE.skillChip;
    const src=bank[m[2].toLowerCase()];
    return src?'<img class="skill-inline" src="'+src+'" alt="'+m[2]+'">'
              :'<span class="gap">'+m[2]+' '+m[1]+'</span>';
  }
  // Real art, extracted from the rulebook back cover. Resource and action
  // tokens are drawn paths; the Mission mark comes from the embedded icon font
  // and is set on a dark chip the way the cards print it.
  if((m=t.match(/^res:(.+)$/))){
    const K={dilithium:'dilithium',latinum:'latinum',glory:'glory-token'}[m[1].toLowerCase()];
    const src=K&&RBICON.token[K];
    return src?'<img class="tokimg" src="'+src+'" alt="'+m[1]+'" title="'+m[1]+'">'
              :'<span class="gap">'+m[1]+' resource</span>';
  }
  if(t==='action'){
    const src=RBICON.token['action'];
    return src?'<img class="tokimg act" src="'+src+'" alt="action" title="Action">'
              :'<span class="gap">action</span>';
  }
  if((m=t.match(/^chip:(.+)$/))){
    const g=RBICON.suit[m[1].toLowerCase().replace(/\s+/g,'-')];
    return '<span class="tok'+(g?'':' plain')+'" style="background:#2b3040">'
      +(g?'<img src="'+g+'" alt="">':'')+m[1].toUpperCase()+'</span>';
  }
  return '<span class="gap">'+t+'</span>';
}

// The transcription is plain text: nobody recorded which words were printed as
// chips or icons. So match them here instead. Suits and traits print as a chip
// carrying BOTH the mark and the word, so those keep their label; resources and
// the action token print as art alone, so the word is replaced outright.
const SUIT_WORDS = Object.keys(SUIT_COL).concat(['Mission']);
const RES_WORDS = {dilithium:'dilithium', latinum:'latinum', glory:'glory-token',
                   action:'action', actions:'action'};
const SPEC = ['Research','Influence','Military','Any','Variable'];

function traitKey(w){
  return w.toLowerCase().replace(/['’]/g,'').replace(/\s+/g,'-');
}

// Trait keys are lowercase letters, digits and hyphens, so no regex escaping is
// needed; building an escape class here is what broke the page once already.
function rx(word, flags){ return new RegExp('\\b' + word + '\\b', flags); }

function autoTokens(text){
  let t = text;
  // longest first, so "Research Skill" wins over a bare "Research"
  SPEC.forEach(sp=>{
    t = t.replace(new RegExp('\\b' + sp + ' (Skill|Focus)\\b','g'),
      (_,k)=>'{' + (k==='Focus'?'focus':'skill') + ':' + sp + '}');
  });
  SUIT_WORDS.forEach(w=>{
    t = t.replace(new RegExp('\\b' + w + 's?\\b','g'),
      ()=>'{' + (w==='Mission'?'chip':'suit') + ':' + w + '}');
  });
  Object.keys(RES_WORDS).forEach(w=>{
    t = t.replace(rx(w,'gi'), m=>/^(dilithium|latinum|glory)$/i.test(m)
      ? '{res:' + m.toLowerCase() + '}' : '{action}');
  });
  // traits last, and only capitalised, so an ordinary "attack" in a sentence
  // stays text while the ATTACK trait becomes a chip
  Object.keys(CARDFACE.traitChip).forEach(k=>{
    t = t.replace(rx(k.replace(/-/g,' '),'gi'),
      m=>(m[0]===m[0].toUpperCase() ? '{trait:' + m + '}' : m));
  });
  return t;
}

function body(text){
  return autoTokens(text)
             .replace(/\{([^}]+)\}/g, (_,t)=>token(t))
             .replace(/_([^_]+)_/g, '<em>$1</em>');
}

function strip(key, mini){
  const p=D.palette[key], lines=D.samples[key]||[];
  const el=document.createElement('div');
  el.className='opstrip'+(mini?' mini':'')+(p.text==='light'?' on-dark':'');
  const ink=p.text==='light'?'#f2f6ff':'#14161c';
  if(p.mode==='inbar'){
    el.classList.add('inbar');
    el.innerHTML=lines.map(([kw,txt])=>
        '<div class="kwblock" style="background:'+p.bar+';color:'+(p.keyword||'#fff')+'">'+kw+':</div>'
      + '<div class="body" style="background:'+p.body+';color:'+ink+'">'+body(txt)+'</div>').join('');
    return el;
  }
  el.innerHTML='<div class="bar" style="background:'+p.bar+'"></div>'
    +'<div class="body" style="background:'+p.body+';color:'+ink+'">'
    + lines.map(([kw,txt,act])=>'<div class="line">'
        +(act&&RBICON.token['action']
            ?'<img class="tokimg act cost" src="'+RBICON.token['action']+'" alt="action cost">':'')
        +(kw?'<span class="kw" style="color:'+(p.keyword||ink)+'">'+kw+':</span> ':'')
        +body(txt)+'</div>').join('')
    +'</div>';
  return el;
}

const out=document.getElementById('out');
D.order.forEach(key=>{
  const p=D.palette[key]; if(!p) return;
  const sec=document.createElement('section');
  sec.innerHTML='<h2>'+p.label+'  &middot;  '+p.card+'</h2>'
    +'<div class="cap">card crop</div>'
    +'<div class="crop"><img src="'+(D.crops[key]||'')+'" alt=""></div>'
    +'<div class="sw"><span><i style="background:'+p.bar+'"></i>bar '+p.bar+'</span>'
    +'<span><i style="background:'+p.body+'"></i>body '+p.body+'</span>'
    +(p.keyword?'<span><i style="background:'+p.keyword+'"></i>keyword '+p.keyword+'</span>':'')
    +'<span>text '+p.text+'</span><span>bar '+p.bar_px+'px of 1170 ('+p.bar_pct+'%)</span></div>'
    +'<div class="cap">full size</div>';
  sec.appendChild(strip(key,false));
  const c=document.createElement('div');
  c.className='cap'; c.textContent='card tile (248px)';
  sec.appendChild(c);
  const tile=document.createElement('div'); tile.className='tilebox';
  tile.appendChild(strip(key,true));
  sec.appendChild(tile);
  out.appendChild(sec);
});
</script></body></html>"""
    html = html.replace('__ASSETS__', assets).replace('__DATA__', json.dumps(data))
    open(out, 'w').write(html)
    print('wrote', out, len(html) // 1024, 'KB')


if __name__ == '__main__':
    main(*sys.argv[1:])
