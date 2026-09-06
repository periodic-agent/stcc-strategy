#!/usr/bin/env node
// Unit tests for the Card Scanner query parser.
// The parser is extracted live from card-browser-mockup.html between the
// QUERY_PARSER_START/END markers, so these tests always exercise the shipped
// code, never a copy. Run from repo root:  node tools/test_scanner_query.mjs

import { readFileSync } from "fs";

const html = readFileSync(new URL("../cards.html", import.meta.url), "utf8");
const m = html.match(/\/\* QUERY_PARSER_START \*\/([\s\S]*?)\/\* QUERY_PARSER_END \*\//);
if (!m) { console.error("FAIL: parser markers not found"); process.exit(1); }
const parseQuery = new Function(m[1] + "; return parseQuery;")();

const vocab = {
  allBoxes: ["core", "tbg", "2nd", "promo1", "promo2"],
  decks: { sisko: "Sisko", georgiou: "Georgiou", common: "::common" },
  suits: { person: "Person", ship: "Ship", "automated command": "Automated Command" },
  tags: { klingon: "Klingon", starfleet: "Starfleet", "mind control": "Mind Control" },
  skills: { "military skill": "Military Skill", "any focus": "Any Focus" },
  skillShort: { military: "Military Skill", variable: "Variable Skill", any: "Any Skill" },
  focusShort: { military: "Military Focus", influence: "Influence Focus", any: "Any Focus" },
  positions: { reserve: "Reserve", "incident deck": "Incident Deck", rewards: "Rewards" },
  stripKinds: { play: true, activation: true, reaction: true, passive: true, cost: true },
};

let failures = 0;
function eq(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function t(name, query, want) {
  const got = parseQuery(query, vocab);
  const bad = Object.keys(want).filter(k => !eq(got[k], want[k]));
  const extra = ["boxes","decks","suits","tags","skills","names",
                 "negBoxes","negDecks","negSuits","negTags","negSkills","negNames",
                 "vp","negVp","positions","negPositions","variants","negVariants",
                 "strips","negStrips","text","negText","kindText","negKindText"]
    .filter(k => !(k in want) && got[k].length);
  if (bad.length || extra.length) {
    failures++;
    console.log("FAIL:", name);
    bad.forEach(k => console.log("  %s: want %j got %j", k, want[k], got[k]));
    extra.forEach(k => console.log("  %s: want [] got %j", k, got[k]));
  } else {
    console.log("ok:", name);
  }
}

t("empty query", "", {});
t("bare name", "kirk", { names: ["kirk"] });
t("two names AND", "orb time", { names: ["orb", "time"] });
t("trait+suit canonical", "trait:klingon suit:person", { tags: ["Klingon"], suits: ["Person"] });
t("case insensitive", "TRAIT:Klingon SUIT:PERSON", { tags: ["Klingon"], suits: ["Person"] });
t("negated trait", "-trait:starfleet", { negTags: ["Starfleet"] });
t("negated bare name", "-kirk", { negNames: ["kirk"] });
t("quoted trait", 'trait:"mind control"', { tags: ["Mind Control"] });
t("quoted skill (long form still works)", 'skill:"military skill"', { skills: ["Military Skill"] });
t("skill shorthand", "skill:military", { skills: ["Military Skill"] });
t("skill variable", "skill:variable", { skills: ["Variable Skill"] });
t("focus shorthand", "focus:military", { skills: ["Military Focus"] });
t("focus negated", "-focus:any", { negSkills: ["Any Focus"] });
t("quoted suit", 'suit:"automated command"', { suits: ["Automated Command"] });
t("deck captain", "deck:sisko", { decks: ["Sisko"] });
t("deck common sentinel", "deck:common", { decks: ["::common"] });
t("box single", "box:tbg", { boxes: ["tbg"] });
t("box list", "box:tbg box:2nd", { boxes: ["tbg", "2nd"] });
t("box all expands", "box:all", { boxes: ["core", "tbg", "2nd", "promo1", "promo2"] });
t("negated box", "-box:tbg", { negBoxes: ["tbg"] });
t("unknown key falls back to name", "foo:bar", { names: ["foo:bar"] });
t("unknown value passes through", "trait:zzz", { tags: ["zzz"] });
t("quoted name phrase", '"orb of"', { names: ["orb of"] });
t("kitchen sink", 'box:tbg deck:georgiou -trait:starfleet skill:"any focus" enterprise',
  { boxes: ["tbg"], decks: ["Georgiou"], negTags: ["Starfleet"],
    skills: ["Any Focus"], names: ["enterprise"] });

// victory points
t("vp equals", "vp:4", { vp: [{ op: "=", n: 4 }] });
t("vp greater, bare operator", "vp>4", { vp: [{ op: ">", n: 4 }] });
t("vp operator after colon", "vp:>=3", { vp: [{ op: ">=", n: 3 }] });
t("vp less or equal", "vp<=2", { vp: [{ op: "<=", n: 2 }] });
t("vp negated", "-vp:1", { negVp: [{ op: "=", n: 1 }] });
t("vp non-numeric ignored", "vp:high", {});
t("victory-points long form", "victory-points:4", { vp: [{ op: "=", n: 4 }] });
t("glory is no longer a key", "glory:4", { names: ["glory:4"] });
t("vp alongside other keys", "vp:4 suit:ship kirk",
  { vp: [{ op: "=", n: 4 }], suits: ["Ship"], names: ["kirk"] });

// position
t("position single word", "position:reserve", { positions: ["Reserve"] });
t("position hyphen for space", "position:incident-deck", { positions: ["Incident Deck"] });
t("position quoted", 'position:"incident deck"', { positions: ["Incident Deck"] });
t("position negated", "-position:rewards", { negPositions: ["Rewards"] });
t("position unknown passes through", "position:zzz", { positions: ["zzz"] });

// variant
t("variant update", "variant:update", { variants: ["update"] });
t("variant updated is the same", "variant:updated", { variants: ["update"] });
t("variant duplicate", "variant:duplicate", { variants: ["duplicate"] });
t("variant reprint is the same", "variant:reprint", { variants: ["duplicate"] });
t("variant negated", "-variant:duplicate", { negVariants: ["duplicate"] });

// strip kinds as text keys
t("kind-scoped phrase", 'reaction:"putting a shady"',
  { kindText: [{ kind: "reaction", term: "putting a shady" }] });
t("kind-scoped single word", "activation:draw",
  { kindText: [{ kind: "activation", term: "draw" }] });
t("kind-scoped negated", "-passive:cloak",
  { negKindText: [{ kind: "passive", term: "cloak" }] });
t("unknown kind is not a key", "sneeze:cloak", { names: ["sneeze:cloak"] });

// sort + dupes toggles
t("sort:position", "sort:position", { sort: "position" });
t("sort short form", "sort:pos", { sort: "pos" });
t("dupes off", "dupes:off", { dupes: false });
t("dupes stays on by default", "kirk", { names: ["kirk"], dupes: true });

if (failures) { console.log(failures + " failure(s)"); process.exit(1); }
console.log("all tests pass");
