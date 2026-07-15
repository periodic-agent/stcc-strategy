#!/usr/bin/env python3
"""ST:CC Compendium guide builder.

Deterministically converts a BGG SingleFile capture of a McCue guide into:
  out/<slug>_text.txt   verbatim text with [[H2]]/[[H3]]/[[B]]/[[I]]/[[IMG:alt]] markers
  out/img/...           card + board images converted to JPG, site naming
  out/<slug>.html       styled guide draft built from tools/guide-template.html
  out/report.txt        image inventory, headers found, warnings

McCue's text is NEVER retyped by hand or by a model: this script moves it
verbatim from the capture into the HTML. Run tools/verify_guide.py afterwards.

Usage:
    python3 build_guide.py <singlefile.html> <config.json> [--out DIR]

Config (see tools/configs/georgiou.json for a real example):
{
  "slug": "georgiou",
  "box": "tbg",                          // core | tbg | sc
  "title_html": "Philippa <span>Georgiou</span>",
  "page_title": "Philippa Georgiou",
  "description": "meta description text",
  "posted": "14 Jul 2026",
  "tags": ["Human", "Starfleet", "Complexity 2/10"],
  "og_image": "img/box2/georgiou-captain-georgiou.jpg",
  "image_names": {                       // optional alt -> filename overrides
      "HC Incident": "hostile-contact",
      "Shenzhou": "uss-shenzhou"
  },
  "board_alts": ["Georgiou Basic", "Georgiou Advanced"],   // -> board-pair, img/guides/<slug>/
  "insert_h2": [                         // structural headers added in formatting
      {"title": "Missions", "before": "Georgiou's player board"},
      {"title": "Captain Card & Starting Components", "before": "Georgiou has five away teams"}
  ],
  "cut": ["To Boldly Go is here"],       // paragraphs to remove (prefix match)
  "lore": ["For our first Captain"],     // force lore styling (prefix match)
  "no_lore": [],                         // prevent auto lore styling (prefix match)
  "toc_labels": {"Georgiou's Reserve Deck Strategy": "Reserve Deck Strategy"},
  "videos": [{"url": "https://youtu.be/WUWw63FQ_Vk",
              "label": "Georgiou Solo Playthrough", "sub": "Solo · Gaming Rules!"}],
  "video_intro": "Playthrough by Paul Grogan (Gaming Rules!) featuring Georgiou:"
}

Stdlib only, except Pillow for WebP -> JPG (falls back to .webp with a warning).
"""

import base64
import html as htmllib
import io
import json
import os
import re
import sys
import unicodedata

BOXES = {
    "core": {"theme": "", "label": "Captain's Chair", "img": "box1"},
    "tbg": {"theme": "theme-tbg", "label": "To Boldly Go", "img": "box2"},
    "sc": {"theme": "theme-sc", "label": "Second Contact", "img": "box3"},
}

APOS = "’"


def plain(t):
    """Apostrophe/quote-insensitive form for prefix matching between
    config strings (straight quotes) and BGG text (curly quotes)."""
    return t.replace(APOS, "'").replace("“", '"').replace("”", '"')


def starts(text, prefixes):
    p = plain(text)
    return any(p.startswith(plain(x)) for x in prefixes)


def slugify(text):
    t = unicodedata.normalize("NFKD", text)
    t = t.replace(APOS, " ").replace("'", " ")
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-{2,}", "-", t)


def extract_post(raw):
    """Return the first gg-markup-content block (balanced) = McCue's post."""
    open_tag = "<gg-markup-content"
    close_tag = "</gg-markup-content>"
    start = raw.find(open_tag + ">")
    if start == -1:
        sys.exit("ERROR: no <gg-markup-content> block found. Is this a SingleFile BGG capture?")
    i, depth = start + len(open_tag) + 1, 1
    while depth:
        o, c = raw.find(open_tag, i), raw.find(close_tag, i)
        if c == -1:
            sys.exit("ERROR: unbalanced gg-markup-content tags.")
        if o != -1 and o < c:
            depth += 1
            i = o + len(open_tag)
        else:
            depth -= 1
            i = c + len(close_tag)
    return raw[start:i]


def extract_images(post, cfg, out_img, report):
    """Decode every <img> (quoted or unquoted src, base64 WebP) to JPG."""
    try:
        from PIL import Image
        have_pil = True
    except ImportError:
        have_pil = False
        report.append("WARNING: Pillow missing; images saved as .webp (site prefers .jpg).")

    slug = cfg["slug"]
    boxdir = BOXES[cfg["box"]]["img"]
    names = cfg.get("image_names", {})
    board_alts = cfg.get("board_alts", [])
    manifest = {}  # alt -> repo-relative path
    for m in re.finditer(r"<img[^>]*>", post):
        tag = m.group(0)
        am = re.search(r'alt="([^"]*)"|alt=([^ >]*)', tag)
        if not am:
            report.append("WARNING: <img> without alt skipped: %s" % tag[:80])
            continue
        alt = (am.group(1) or am.group(2)).strip()
        # SingleFile sometimes appends attribute junk to unquoted alts
        alt = re.sub(r"\s+(sizes|content)=.*$", "", alt).strip()
        b64 = re.search(r'src="?data:image/webp;base64,([A-Za-z0-9+/=]+)', tag)
        cdn = re.search(r'content="?(https://cf\.geekdo-images\.com[^" >]+)', tag)
        if not b64:
            report.append("WARNING: no base64 for '%s'; CDN fallback: %s" % (alt, cdn.group(1) if cdn else "none"))
            continue
        base = names.get(alt, slugify(alt))
        if alt in board_alts:
            side = "advanced" if re.search(r"advanced", alt, re.I) else "basic"
            rel = "img/guides/%s/%s-board-%s.jpg" % (slug, slug, side)
        else:
            fname = base if base.startswith(slug + "-") else "%s-%s" % (slug, base)
            rel = "img/%s/%s.jpg" % (boxdir, fname)
        path = os.path.join(out_img, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = base64.b64decode(b64.group(1))
        if have_pil:
            from PIL import Image
            img = Image.open(io.BytesIO(data))
            img.convert("RGB").save(path, "JPEG", quality=90)
            report.append("image  %-30s -> %s  %s" % (alt, rel, img.size))
        else:
            path = path[:-4] + ".webp"
            rel = rel[:-4] + ".webp"
            open(path, "wb").write(data)
            report.append("image  %-30s -> %s (webp)" % (alt, rel))
        manifest[alt] = rel
    return manifest


def header_sizes(post):
    sizes = sorted({float(s) for s in re.findall(r"font-size:([\d.]+)px", post)}, reverse=True)
    h2 = sizes[0] if sizes else None
    h3 = sizes[1] if len(sizes) > 1 else None
    return h2, h3


def to_marked_text(post):
    """Verbatim text with structural markers. Every character of McCue's
    prose survives untouched; only tags become markers."""
    h2, h3 = header_sizes(post)
    s = post
    s = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', lambda m: "\n[[IMG:%s]]\n" % m.group(1).strip(), s)
    s = re.sub(r"<img[^>]*alt=([^ >]*)[^>]*>", lambda m: "\n[[IMG:%s]]\n" % m.group(1).strip(), s)
    if h2 is not None:
        s = re.sub(r"<span style=[^>]*font-size:%spx[^>]*>(.*?)</span>" % re.escape("%.2f" % h2),
                   r"\n[[H2]]\1[[/H2]]\n", s, flags=re.S)
    if h3 is not None:
        s = re.sub(r"<span style=[^>]*font-size:%spx[^>]*>(.*?)</span>" % re.escape("%.2f" % h3),
                   r"\n[[H3]]\1[[/H3]]\n", s, flags=re.S)
    # strip formatting wrappers hugging headers (strong / underline spans)
    s = re.sub(r"<(strong|span style=text-decoration:underline)>\s*(\[\[H[23]\]\])", r"\2", s)
    s = re.sub(r"(\[\[/H[23]\]\])\s*</(strong|span)>", r"\1", s)
    # links -> markers
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[[A:\1]]\2[[/A]]", s, flags=re.S)
    s = re.sub(r"<br[^>]*>", "\n", s)
    s = s.replace("<strong>", "[[B]]").replace("</strong>", "[[/B]]")
    s = s.replace("<em>", "[[I]]").replace("</em>", "[[/I]]")
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s)
    # drop lines that are only orphaned markers left by header stripping
    s = re.sub(r"^\s*\[\[/?[BI]\]\]\s*$", "", s, flags=re.M)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def fmt_inline(t):
    t = htmllib.escape(t.strip(), quote=False)
    t = t.replace("[[B]]", "<strong>").replace("[[/B]]", "</strong>")
    t = t.replace("[[I]]", "<em>").replace("[[/I]]", "</em>")
    t = re.sub(r"\[\[A:([^\]]+)\]\]", r'<a href="\1" target="_blank" rel="noopener">', t)
    t = t.replace("[[/A]]", "</a>")
    return t



def _apply_repl(text, pairs):
    for a, to in pairs:
        text = text.replace(a, to)
    return text


def build_body(marked, cfg, manifest, report):
    """Emit <main> body HTML plus the H2 list for the TOC."""
    slug = cfg["slug"]
    board_alts = set(cfg.get("board_alts", []))
    cuts = cfg.get("cut", [])
    force_lore = cfg.get("lore", [])
    no_lore = cfg.get("no_lore", [])
    inserts = list(cfg.get("insert_h2", []))

    # tokenize
    tokens = []
    for line in marked.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\[\[IMG:(.*)\]\]$", line)
        if m:
            alt = re.sub(r"\s+(sizes|content)=.*$", "", m.group(1)).strip()
            tokens.append(("img", alt))
            continue
        m = re.match(r"^\[\[H2\]\](.*)\[\[/H2\]\]$", line)
        if m:
            tokens.append(("h2", m.group(1).strip()))
            continue
        m = re.match(r"^\[\[H3\]\](.*)\[\[/H3\]\]$", line)
        if m:
            tokens.append(("h3", m.group(1).strip()))
            continue
        tokens.append(("p", line))

    # sanctioned corrections (config "replace": [[from, to], ...]);
    # use these ONLY for fixes Periodic_agent/McCue explicitly approved.
    repl = cfg.get("replace", [])
    tokens = [(k, _apply_repl(v, repl) if k != "img" else v) for k, v in tokens]

    # cuts + inserted structural H2s
    out = []
    for kind, val in tokens:
        if kind == "p" and starts(val, cuts):
            report.append("cut    %s..." % val[:60])
            continue
        ins = next((i for i in inserts if kind == "p" and starts(val, [i["before"]])), None)
        if ins:
            out.append(("h2", ins["title"]))
            inserts.remove(ins)
        out.append((kind, val))
    for i in inserts:
        report.append("WARNING: insert_h2 anchor not found: %s" % i["before"])
    tokens = out

    # merge board images (may be separated by prose) into one pair group
    # at the position of the first board image
    board_idxs = [i for i, t in enumerate(tokens) if t[0] == "img" and t[1] in board_alts]
    if len(board_idxs) >= 2:
        boards = [tokens[i][1] for i in board_idxs]
        first = board_idxs[0]
        tokens = [t for i, t in enumerate(tokens) if i not in board_idxs[1:]]
        tokens[first] = ("imgs", boards)

    # group consecutive images
    grouped, i = [], 0
    while i < len(tokens):
        if tokens[i][0] == "img":
            j = i
            alts = []
            while j < len(tokens) and tokens[j][0] == "img":
                alts.append(tokens[j][1])
                j += 1
            grouped.append(("imgs", alts))
            i = j
        elif tokens[i][0] == "imgs":
            alts = list(tokens[i][1])
            j = i + 1
            while j < len(tokens) and tokens[j][0] in ("img", "imgs"):
                alts.extend([tokens[j][1]] if tokens[j][0] == "img" else tokens[j][1])
                j += 1
            grouped.append(("imgs", alts))
            i = j
        else:
            grouped.append(tokens[i])
            i += 1
    tokens = grouped

    # image group directly before a heading belongs to that heading's
    # section -> move it after the heading (BGG posts put images above
    # the header line; the site puts them below it).
    out = []
    for tok in tokens:
        if out and out[-1][0] == "imgs" and tok[0] in ("h2", "h3"):
            imgs = out.pop()
            out.append(tok)
            out.append(imgs)
        else:
            out.append(tok)
    tokens = out

    def render_imgs(alts):
        missing = [a for a in alts if a not in manifest]
        for a in missing:
            report.append("WARNING: no image file for alt '%s'" % a)
        alts = [a for a in alts if a in manifest]
        if not alts:
            return ""
        if any(a in board_alts for a in alts) and len(alts) == 2:
            basic, adv = alts if "basic" in manifest[alts[0]] else (alts[1], alts[0])
            return ('  <div class="board-pair">\n'
                    '    <div>\n      <img src="%s" alt="%s Captain Board" loading="lazy" onclick="openLightbox(this)">\n'
                    '      <div class="board-label">Basic Side</div>\n    </div>\n'
                    '    <div>\n      <img src="%s" alt="%s Captain Board" loading="lazy" onclick="openLightbox(this)">\n'
                    '      <div class="board-label">Advanced Side</div>\n    </div>\n  </div>\n'
                    % (manifest[basic], basic, manifest[adv], adv))
        if len(alts) == 1:
            a = alts[0]
            return ('<div class="card-img"><img src="%s" alt="%s" loading="lazy" onclick="openLightbox(this)"></div>\n'
                    % (manifest[a], a))
        rows = "".join('    <img src="%s" alt="%s" loading="lazy" onclick="openLightbox(this)">\n'
                       % (manifest[a], a) for a in alts)
        return '  <div class="card-row">\n%s  </div>\n' % rows

    def is_lore(text):
        if starts(text, no_lore):
            return False, text
        if starts(text, force_lore):
            return True, text
        m = re.match(r"^\[\[I\]\](.*)\[\[/I\]\]\s*$", text, re.S)
        if m:
            inner = m.group(1)
            # only strip the outer wrap if it truly encloses the paragraph
            # (first inner close must come after first inner open)
            c, o = inner.find("[[/I]]"), inner.find("[[I]]")
            if c == -1 or (o != -1 and o < c):
                return True, inner.strip()
        return False, text

    BT = '  <a href="#top" class="back-top">↑ back to top</a>\n'
    body, h2s, since_heading = [], [], 0
    first_h2_seen = False
    for kind, val in tokens:
        if kind in ("h2", "h3") and since_heading:
            body.append(BT)
            since_heading = 0
        if kind == "h2":
            if not first_h2_seen and body:
                pass  # Introduction handled below
            hid = slugify(val)
            h2s.append((hid, val))
            body.append('\n  <h2 id="%s">%s</h2>\n\n' % (hid, fmt_inline(val)))
            first_h2_seen = True
        elif kind == "h3":
            body.append("<h3>%s</h3>\n" % fmt_inline(val))
        elif kind == "imgs":
            body.append(render_imgs(val))
        else:
            lore, text = is_lore(val)
            klass = ' class="lore"' if lore else ""
            body.append("  <p%s>%s</p>\n" % (klass, fmt_inline(text)))
            since_heading += 1
    if since_heading:
        body.append(BT)

    # untitled leading section -> Introduction
    if body and not body[0].lstrip().startswith("<h2") and not body[0].lstrip().startswith("\n  <h2"):
        body.insert(0, "  <h2>Introduction</h2>\n\n")
    return "".join(body), h2s


def build_toc(h2s, cfg):
    labels = cfg.get("toc_labels", {})
    items = ['    <li><a href="#%s">%s</a></li>' % (hid, fmt_inline(labels.get(title, title)))
             for hid, title in h2s]
    if cfg.get("videos"):
        items.append('    <li><a href="#video-playthroughs">Video Playthroughs</a></li>')
    return "\n".join(items)


def build_video(cfg):
    vids = cfg.get("videos", [])
    if not vids:
        return ""
    cards = []
    for v in vids:
        vid = re.search(r"(?:youtu\.be/|v=|live/)([\w-]+)", v["url"]).group(1)
        cards.append(
            '    <a href="%s" target="_blank" class="yt-card">\n'
            '      <div class="yt-thumb">\n'
            '        <img src="https://img.youtube.com/vi/%s/mqdefault.jpg" alt="%s thumbnail">\n'
            '        <div class="yt-play">▶</div>\n      </div>\n'
            '      <div class="yt-label">%s</div>\n'
            '      <div class="yt-sub">%s</div>\n    </a>\n'
            % (v["url"], vid, v["label"], v["label"], v.get("sub", "")))
    intro = cfg.get("video_intro", "")
    intro_html = "  <p>%s</p>\n\n" % intro if intro else ""
    return ('\n  <h2 id="video-playthroughs">Video Playthroughs</h2>\n\n%s'
            '  <div class="yt-grid">\n\n%s\n  </div>\n' % (intro_html, "".join(cards)))


def main():
    argv, args, out_dir = sys.argv[1:], [], "out"
    i = 0
    while i < len(argv):
        if argv[i] == "--out":
            out_dir = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 2:
        sys.exit(__doc__)
    src_path, cfg_path = args
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    raw = open(src_path, encoding="utf-8", errors="replace").read()
    os.makedirs(out_dir, exist_ok=True)
    report = []

    post = extract_post(raw)
    report.append("post block: %d bytes" % len(post))
    if "@mdmccu2" not in raw[:raw.find("<gg-markup-content>")]:
        report.append("WARNING: could not confirm @mdmccu2 as author of first post.")

    manifest = extract_images(post, cfg, out_dir, report)
    marked = to_marked_text(post)
    open(os.path.join(out_dir, "%s_text.txt" % cfg["slug"]), "w", encoding="utf-8").write(marked)

    body, h2s = build_body(marked, cfg, manifest, report)
    box = BOXES[cfg["box"]]
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "guide-template.html"),
               encoding="utf-8").read()
    page = (tpl.replace("{{SLUG}}", cfg["slug"])
               .replace("{{PAGE_TITLE}}", cfg["page_title"])
               .replace("{{DESCRIPTION}}", cfg["description"])
               .replace("{{OG_IMAGE}}", cfg.get("og_image", ""))
               .replace("{{THEME_CLASS}}", (" class=\"%s\"" % box["theme"]) if box["theme"] else "")
               .replace("{{CHAPTER_LABEL}}", box["label"])
               .replace("{{TITLE_HTML}}", cfg["title_html"])
               .replace("{{POSTED}}", cfg["posted"])
               .replace("{{TAGS}}", "".join('<span class="tag">%s</span>' % t for t in cfg.get("tags", [])))
               .replace("{{TOC}}", build_toc(h2s, cfg))
               .replace("{{BODY}}", body)
               .replace("{{VIDEO_SECTION}}", build_video(cfg)))
    out_html = os.path.join(out_dir, "%s.html" % cfg["slug"])
    open(out_html, "w", encoding="utf-8").write(page)
    report.append("guide: %s (%d bytes), %d H2 sections, %d images"
                  % (out_html, len(page), len(h2s), len(manifest)))
    open(os.path.join(out_dir, "report.txt"), "w", encoding="utf-8").write("\n".join(report))
    print("\n".join(report))
    print("\nNext: python3 tools/verify_guide.py %s %s --config %s"
          % (out_html, os.path.join(out_dir, "%s_text.txt" % cfg["slug"]), cfg_path))


if __name__ == "__main__":
    main()
