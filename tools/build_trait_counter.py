#!/usr/bin/env python3
"""Build the Archer Trait Counter tool page.

Reads the canonical card JSONs at repo root to derive the trait universe and
per-box membership, and cardface-assets.js for the trait chip medallions.
The chips are downscaled to 44 px and colour-quantised so the page can carry
them inline (~90 KB total) instead of pulling the 1.9 MB scanner asset bundle.

Usage:  python3 tools/build_trait_counter.py [--repo .] [--out archer-scoring.html]

Rule 7: this script ships in tools/ in the same commit as its output.
"""
import argparse, base64, io, json, os, re, sys
from PIL import Image

BOXES = [("core", "box1.json"), ("tbg", "box2.json"), ("2nd", "box3.json"),
         ("promo1", "promo1.json"), ("promo2", "promo2.json")]
GROUP_KEYS = [("species", "species_traits"), ("regular", "regular_traits"),
              ("other", "other_traits")]
ICON_PX = 44
# Traits Archer can never have in play because they exist only inside another
# captain's deck. Confirmed against the card data, not assumed.
EXCLUDE = {"Path of Surak"}
ICON_COLORS = 64


def slug(name):
    return name.lower().replace("'", "").replace("\u2019", "").replace(" ", "-")


def read_traits(repo):
    taxonomy, membership = {}, {}
    for bkey, fname in BOXES:
        path = os.path.join(repo, fname)
        for card in json.load(open(path, encoding="utf-8")):
            for group, key in GROUP_KEYS:
                for t in (card.get(key) or []):
                    taxonomy[t] = group
                    membership.setdefault(t, set()).add(bkey)
    return taxonomy, membership


def read_icons(repo, wanted):
    src = open(os.path.join(repo, "cardface-assets.js"), encoding="utf-8").read()
    m = re.search(r"const CARDFACE=(\{.*\});?\s*$", src, re.S)
    if not m:
        sys.exit("cardface-assets.js: CARDFACE object not found")
    chips = json.loads(m.group(1))["traitChip"]
    out = {}
    for name in wanted:
        s = slug(name)
        if s not in chips:
            sys.exit("no trait chip for %r (slug %r)" % (name, s))
        raw = base64.b64decode(chips[s].split(",", 1)[1])
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        im = im.resize((ICON_PX, ICON_PX), Image.LANCZOS)
        im = im.quantize(colors=ICON_COLORS, method=Image.FASTOCTREE)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        out[s] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return out


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>ST:CC Archer Trait Counter</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Exo+2:wght@300;400;600&family=Antonio:wght@600&family=Barlow+Condensed:wght@500;600&display=swap" rel="stylesheet">
<script data-goatcounter="https://stcc-compendium.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<style>
:root{
  --bg:#0a0e1a;--bg2:#0f1628;--bg3:#141c35;
  --tool:#d44a4a;--tool2:#f07e7e;
  --gold:#c8a84b;--text:#ccd6f0;--muted:#7a8aaa;--green:#4ac48a;
  --border:rgba(212,74,74,0.25);
}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Exo 2',sans-serif;font-weight:300;background:var(--bg);color:var(--text);min-height:100vh;}
a{color:var(--tool2);text-decoration:none;}
.nav-bar{background:var(--bg);border-bottom:1px solid var(--border);padding:0.75rem 1.5rem;display:flex;gap:1.25rem;flex-wrap:wrap;}
.nav-bar a{font-family:'Orbitron',sans-serif;font-size:0.65rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--tool2);}
.chapter-header{background:linear-gradient(135deg,#160608 0%,#2a0e10 50%,#160608 100%);border-bottom:2px solid var(--tool);padding:1.2rem 2rem 1rem;text-align:center;position:relative;overflow:hidden;}
.chapter-header::before{content:'';position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent,transparent 60px,rgba(212,74,74,0.03) 60px,rgba(212,74,74,0.03) 61px);}
.chapter-label{font-family:'Orbitron',sans-serif;font-size:0.7rem;letter-spacing:0.25em;color:var(--tool);text-transform:uppercase;margin-bottom:0.6rem;position:relative;}
.chapter-title{font-family:'Orbitron',sans-serif;font-size:clamp(1.4rem,4vw,2.2rem);font-weight:700;color:#fff;letter-spacing:0.05em;text-shadow:0 0 40px rgba(212,74,74,0.4);position:relative;}
.chapter-title span{color:var(--tool2);}
.chapter-meta{margin-top:0.5rem;font-size:0.78rem;color:var(--muted);position:relative;}

/* ---- sticky scoreboard ---- */
.score{position:sticky;top:0;z-index:40;background:rgba(10,14,26,0.96);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--border);padding:0.6rem 1.5rem;}
.score-inner{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:1.1rem;flex-wrap:wrap;}
.vp-block{display:flex;align-items:baseline;gap:0.45rem;}
.vp-num{font-family:'Orbitron',sans-serif;font-weight:700;font-size:2.4rem;line-height:1;color:var(--gold);
  min-width:1.6ch;text-align:right;}
.vp-lbl{font-family:'Orbitron',sans-serif;font-weight:400;font-size:0.7rem;letter-spacing:0.2em;text-transform:uppercase;color:var(--gold);}
.score-sub{display:flex;flex-direction:column;gap:0.2rem;font-size:0.78rem;line-height:1.35;color:var(--muted);}
.score-sub span{font-family:'Exo 2',sans-serif;font-weight:300;letter-spacing:0.02em;}
.score-sub b{font-weight:600;color:var(--text);}
.score-next.ready b{color:var(--green);}
.meter{flex:1 1 180px;min-width:150px;height:6px;border-radius:3px;background:rgba(255,255,255,0.07);overflow:hidden;}
.meter i{display:block;height:100%;width:0;background:var(--gold);opacity:0.75;transition:width 0.18s;}
.btn-reset{font-family:'Orbitron',sans-serif;font-size:0.55rem;letter-spacing:0.15em;text-transform:uppercase;
  padding:0.35rem 0.8rem;border:1px solid var(--border);border-radius:3px;background:transparent;color:var(--muted);cursor:pointer;}
.btn-reset:hover{border-color:var(--tool);color:var(--tool2);}

/* ---- layout ---- */
.wrap{max-width:1100px;margin:1.25rem auto 0;padding:0 1.5rem;}

/* ---- trait chips (identical geometry to the Card Scanner) ---- */
.section{margin-top:1.5rem;}
.sec-head{display:flex;align-items:baseline;gap:0.6rem;margin-bottom:0.55rem;}
.sec-title{font-family:'Orbitron',sans-serif;font-size:0.6rem;letter-spacing:0.2em;text-transform:uppercase;color:var(--muted);}
.sec-tally{font-family:'Antonio',sans-serif;font-size:0.8rem;color:var(--muted);}
.chips{display:flex;flex-wrap:wrap;gap:0.4rem;}
.cardpill{display:inline-flex;align-items:center;gap:.4rem;border-radius:999px;
  height:26px;box-sizing:border-box;padding:0 .6rem 0 .12rem;cursor:pointer;user-select:none;
  font-family:'Antonio',sans-serif;font-weight:600;font-size:.9rem;letter-spacing:.03em;
  line-height:1;text-transform:uppercase;background:transparent;
  border:1.5px solid var(--cc,#8494ad);color:var(--cc,#8494ad);transition:background 0.12s;}
.cardpill img{height:23px;width:23px;}
.cardpill:hover{background:rgba(255,255,255,.07);}
.cardpill.active{background:var(--cc,#8494ad) !important;color:#fff !important;}
.cp-species{--cc:#e2a04a;}
.cp-regular{--cc:#79b3c7;}
.cp-other{--cc:#c85340;}
.cp-wild{--cc:#eef1f6;}
.cp-wild.active{color:#20242e !important;}

/* ---- Endgame box: mimics the printed operation box on the captain card.
   Colours sampled from img/box2/archer-jonathan-archer.jpg and corrected for
   the scan white point (the near-white RESUPPLY box reads 197,201,186). ---- */
.endgame{margin-top:1.6rem;max-width:720px;display:flex;background:#eecac7;
  border-radius:0 7px 7px 0;overflow:hidden;}
.endgame-bar{flex:none;width:6px;background:#e03511;}
.endgame-body{padding:0.55rem 0.9rem 0.6rem;font-family:'Barlow Condensed',sans-serif;
  font-weight:500;font-size:1.15rem;line-height:1.32;color:#14161c;}
.endgame-body .eg{font-family:'Antonio',sans-serif;font-weight:600;color:#e03511;
  letter-spacing:0.02em;text-shadow:0 0 2px #fff,0 0 5px rgba(255,255,255,0.9);}
.glory-inline{height:1.3em;width:auto;vertical-align:-0.3em;margin:0 0.06em;}

footer{margin-top:2.5rem;border-top:1px solid var(--border);padding:1.25rem 1.5rem;text-align:center;font-size:0.72rem;color:var(--muted);line-height:1.8;}

@media(max-width:600px){
  .wrap{padding:0 1rem;}
  .score{padding:0.5rem 1rem;}
  .vp-num{font-size:2rem;}
  .meter{flex-basis:100%;order:5;}
  .cardpill{height:28px;font-size:.92rem;}
  .cardpill img{height:25px;width:25px;}
}
</style>
</head>
<body>

<div class="nav-bar">
  <a href="index.html">&#8592; Back to Compendium</a>
  <a href="cards.html">Card Scanner</a>
</div>

<div class="chapter-header">
  <div class="chapter-label">Tool</div>
  <h1 class="chapter-title">Archer <span>Trait Counter</span></h1>
  <div class="chapter-meta">Tap every trait you have in play. One tap per trait, so nothing gets counted twice.</div>
</div>

<div class="score">
  <div class="score-inner">
    <div class="vp-block"><span class="vp-num" id="vp">0</span><span class="vp-lbl">VP</span></div>
    <div class="score-sub">
      <span class="score-count"><b id="nsel">0</b> unique traits selected</span>
      <span class="score-next" id="next"><b>3</b> more traits to 1 VP</span>
    </div>
    <div class="meter"><i id="bar"></i></div>
    <button class="btn-reset" id="reset">Clear</button>
  </div>
</div>

<div class="wrap">

  <div class="section" id="sec-species">
    <div class="sec-head"><span class="sec-title">Species Traits</span><span class="sec-tally" id="tally-species"></span></div>
    <div class="chips" id="chips-species"></div>
  </div>

  <div class="section" id="sec-regular">
    <div class="sec-head"><span class="sec-title">Regular Traits</span><span class="sec-tally" id="tally-regular"></span></div>
    <div class="chips" id="chips-regular"></div>
  </div>

  <div class="section" id="sec-other">
    <div class="sec-head"><span class="sec-title">Other Traits</span><span class="sec-tally" id="tally-other"></span></div>
    <div class="chips" id="chips-other"></div>
  </div>

  <div class="endgame">
    <div class="endgame-bar"></div>
    <div class="endgame-body"><span class="eg">ENDGAME:</span> Score <svg class="glory-inline" viewBox="0 0 32 29" role="img" aria-label="1 Glory"><ellipse cx="16" cy="14.5" rx="15.5" ry="11" fill="#fff"/><path transform="translate(16 14.5) scale(1.7) translate(-13 -11.65)" d="M13 3.6c2.3 4 5.2 10.2 7.5 16.1-2.7-2-5.1-2.9-7.5-2.9s-4.8.9-7.5 2.9C7.8 13.8 10.7 7.6 13 3.6z" fill="#c3cfdd"/><text x="16" y="21.7" text-anchor="middle" font-size="20" font-weight="700" fill="#10161f" font-family="Antonio,sans-serif">1</text></svg> for every 3 unique traits you have in play.</div>
  </div>

</div>

<footer>Card images &copy; WizKids.<br>Unofficial fan content.</footer>

<script>
const TRAITS = __TRAITS__;
const ICONS = __ICONS__;
const DIVISOR = 3;

let sel = new Set();

function slug(n){ return n.toLowerCase().replace(/['\u2019]/g,"").replace(/\s+/g,"-"); }
function counted(t){ return sel.has(t.name); }

function buildChips(){
  ["species","regular","other"].forEach(g => {
    const host = document.getElementById("chips-" + g);
    host.innerHTML = "";
    TRAITS.filter(t => t.group === g).sort((a,b) => a.name.localeCompare(b.name)).forEach(t => {
      const p = document.createElement("span");
      let cc = g === "species" ? "cp-species" : g === "other" ? "cp-other" : "cp-regular";
      if (t.name === "Wildcard") cc = "cp-wild";
      p.className = "cardpill " + cc;
      p.dataset.name = t.name;
      const ic = ICONS[slug(t.name)];
      p.innerHTML = (ic ? '<img src="' + ic + '" alt="">' : "") + "<span>" + t.name + "</span>";
      p.onclick = () => { sel.has(t.name) ? sel.delete(t.name) : sel.add(t.name); render(); };
      host.appendChild(p);
    });
  });
}

function render(){
  let n = 0;
  const groupTotals = {species:[0,0], regular:[0,0], other:[0,0]};
  TRAITS.forEach(t => {
    const el = document.querySelector('.cardpill[data-name="' + t.name.replace(/"/g,'\\"') + '"]');
    if (!el) return;
    el.classList.toggle("active", sel.has(t.name));
    groupTotals[t.group][1]++;
    if (sel.has(t.name)) { groupTotals[t.group][0]++; n++; }
  });
  ["species","regular","other"].forEach(g => {
    const [a, b] = groupTotals[g];
    document.getElementById("tally-" + g).textContent = a + " / " + b;
  });

  const vp = Math.floor(n / DIVISOR);
  const rem = n % DIVISOR;
  const need = DIVISOR - rem;
  document.getElementById("vp").textContent = vp;
  document.getElementById("nsel").textContent = n;
  const nx = document.getElementById("next");
  nx.innerHTML = "<b>" + need + "</b> more trait" + (need === 1 ? "" : "s") + " to " + (vp + 1) + " VP";
  nx.classList.toggle("ready", need === 1);
  document.getElementById("bar").style.width = (rem / DIVISOR * 100) + "%";
  writeHash();
}

function writeHash(){
  const parts = [];
  if (sel.size) parts.push("t=" + [...sel].map(slug).join(","));
  const h = parts.join("&");
  // Sandboxed previews (opaque origin, about:srcdoc, blob:) refuse history
  // access and throw SecurityError. The hash is a convenience, not state, so
  // failing to write it must not surface as an uncaught error.
  try {
    if (h) history.replaceState(null, "", "#" + h);
    else if (location.hash) history.replaceState(null, "", location.pathname + location.search);
  } catch (e) { /* no address-bar sync available; in-memory state is unaffected */ }
}

function readHash(){
  const h = location.hash.replace(/^#/, "");
  if (!h) return;
  const q = Object.fromEntries(h.split("&").map(s => s.split("=")));
  if (q.t) {
    const bySlug = {};
    TRAITS.forEach(t => bySlug[slug(t.name)] = t.name);
    q.t.split(",").forEach(s => { if (bySlug[s]) sel.add(bySlug[s]); });
  }
}

document.getElementById("reset").onclick = () => { sel.clear(); render(); };

buildChips();
readHash();
render();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="archer-scoring.html")
    a = ap.parse_args()

    taxonomy, membership = read_traits(a.repo)
    icons = read_icons(a.repo, [t for t in taxonomy if t not in EXCLUDE])
    traits = [{"name": n, "group": taxonomy[n]}
              for n in sorted(taxonomy) if n not in EXCLUDE]

    html = (TEMPLATE
            .replace("__TRAITS__", json.dumps(traits, ensure_ascii=False))
            .replace("__ICONS__", json.dumps(icons)))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    counts = {}
    for t in traits:
        counts[t["group"]] = counts.get(t["group"], 0) + 1
    print("wrote %s  (%d traits: %s)  %.0f KB"
          % (a.out, len(traits), counts, os.path.getsize(a.out) / 1024))


if __name__ == "__main__":
    main()
