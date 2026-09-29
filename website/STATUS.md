# Bible website — status

SDLC workflow: `bible-website` (saved workflow `~/.jarvis/workflows/bible-website.js`).
Spec (Kit, 2026-09-22): drop-down over each Hebrew word — KJV rendering, Young's rendering,
Other (user-defined, the academic pass). Browse book → chapter → verse → words.
Choosing word by word builds and saves his translation.

Corpus `bible.db` stays READ-ONLY. Website storage:
- `app.db`: `app_user`, `translation`, `other_option` (multi-value "Other" renderings).
- `user_data/translation_<id>.choices`: ONE BYTE PER WORD (264,217 bytes),
  byte at offset (word_id − 1). Byte = drop-down item number selected:
  0 = default (no choice); rest index into the word's drop-down list rebuilt
  identically as [KJV renderings | Young's-computed renderings | Other options].

## Log

- 2026-09-22 ~03:30 PT: project ordered ("let's build it"); SDLC invoked.
  Design phase: website ER diagram + system diagram drawn
  (`website/website_er.png`, `website/website_system.png`; builder `website_diagrams.py`).
- 2026-09-22 ~03:27 PT: YLT word alignment in progress (`build_ylt_align.py`):
  verse-by-verse, YLT tokens ↔ KJV tokens (monolingual Needleman-Wunsch),
  KJV → Hebrew via shared Strong's. Output `ylt_renderings(word_id, ylt_word, ylt_word_pos)`.
  COMPUTED best-effort, not a source alignment.
- Implementation / test / verify phases: not started.
- 2026-09-22 ~03:40 PT: YLT alignment COMPLETE (exit 0, 232s): 23,006 verses,
  598,514 YLT tokens, 215,533 mapped to Hebrew (36.0%); 262,062 Hebrew words,
  114,269 with >=1 YLT word (43.6%); 259,171 ylt_renderings rows.
  Coverage honest-measured (measure_ylt_coverage.py): per-book Hebrew-word hit
  26.8% (Joel) to 52.9% (Ezra); 56.8% of Hebrew words have no YLT rendering,
  59.2% of those unbridgeable (blank Strong's). 65.1% of hit words map to >1
  distinct YLT word. Spot-checks (Ex 20:2, Ps 23:1, Isa 53:5, Obad 1:1) show
  real errors (e.g. H3068 -> "from", H2637 -> "not"). COMPUTED, not authoritative.
- 2026-09-22 ~03:45 PT: lexicon.ylt_renderings_computed added
  (build_lexicon_ylt.py): 62,323/126,869 rows (49.1%), frequency-ordered,
  ' | '-separated, labeled computed.
- 2026-09-22 ~03:50 PT: website/schema.sql created (app_user, translation,
  translation_choice with chosen_source IN ('kjv','ylt','other'),
  UNIQUE(translation_id, word_id)).
- 2026-09-22 ~03:55 PT: Flask app built (website/app.py, port 5057): routes /,
  /book/<n>, /chapter/<n>/<c>, /verse/<n>/<c>/<v> (per-word KJV/Young's-computed/
  Other dropdown + save), POST /choice, /translations (create/select),
  /reading/<tid>/<n>/<c>/<v>, /export/<tid>, /word/<wid> (pointed/unpointed,
  letters, root code, Strong's, renderings, contexts, verses).
- 2026-09-22 ~04:00 PT: tested locally end-to-end: all routes 200; created
  translation, saved KJV + Other choices, verified persistence (2 checks),
  reading view composes, export downloads, word detail renders. Test data
  removed (app.db deleted; recreated on first run).
- 2026-09-22 ~03:45 PT (Kit's directive: "a byte per word"): choice storage
  redesigned from SQL rows to a flat index file — `user_data/translation_<id>.choices`,
  264,217 bytes, byte at offset (word_id − 1) = selected drop-down item number
  (0 = default; rest index into [KJV | Young's-computed | Other options]).
  `translation_choice` table replaced by `other_option` (multi-value Other
  renderings). ER + system diagrams redrawn (`website_diagrams.py`) showing the
  byte file. Retested end-to-end: byte file correct on disk, other_option row
  saved, verse/reading/export all resolve bytes correctly. Test data removed.

## 2026-09-22 ~04:10 PT — GitHub push recovered (59854d4)
- Push had been failing: the cleanup commit accidentally staged bible.db (175MB)
  and four bible.db.bak-* files (76-162MB) via `git add -A` after an earlier
  `.gitignore` overwrite dropped the `*.db` rule. GitHub rejects files >100MB.
- Fixed: removed all five from the commit, restored the merged `.gitignore`
  (`*.db`, `*.bak*`, `worker-out/`, `website/venv/`, `website/app.db`,
  `website/user_data/`, `__pycache__/`, `*.pyc`).
- Also folded in the Unlicense (public domain dedication) commit.
- Recommitted as ONE commit on top of public 3925d68 (no history rewrite):
  `59854d4 Byte-per-word choice index + venv removed from repo + Unlicense`.
- Remote master verified at 59854d4: no website/venv, no bible.db or .bak files,
  LICENSE + byte-design app/diagrams/docs all present.
- Note: website/venv blobs remain inside the earlier public 3925d68 snapshot
  (deleted at tip). Full history purge would need a force-push; parked unless
  Kit wants it.

## 2026-09-22 ~04:20 PT — Diagrams as text (Mermaid sources)
- Kit sent a link to the "text to UML tools" list (diagrams-as-code).
- Added `website/website_er.mmd` (erDiagram: app.db + choice files) and
  `website/website_system.mmd` (flowchart: browser -> Flask -> three stores),
  faithful to the matplotlib PNG/SVG versions.
- README.md now embeds both as ```mermaid fences (rendered live on GitHub)
  via a Diagrams section; the .mmd files are the text sources and a small
  injector keeps the README copies in sync.
- PNG/SVG outputs kept as-is.
- Render validation 2026-09-22 ~03:58 PT: both .mmd files render clean via
  mermaid-cli (first attempt needed a --no-sandbox puppeteer config since the
  sandbox runs as root). ER diagram visually inspected; system diagram SVG
  node/edge/label text inspected. GitHub will render the README embeds live.

## 2026-09-22 ~04:20 PT — Diagrams as text (Mermaid sources)
- Kit sent a link to the "text to UML tools" list (diagrams-as-code).
- Added `website/website_er.mmd` (erDiagram: app.db + choice files) and
  `website/website_system.mmd` (flowchart: browser -> Flask -> three stores),
  faithful to the matplotlib PNG/SVG versions.
- README.md now embeds both as ```mermaid fences (rendered live on GitHub)
  via a Diagrams section; the .mmd files are the text sources and a small
  injector keeps the README copies in sync.
- PNG/SVG outputs kept as-is.
- Render validation 2026-09-22 ~03:58 PT: both .mmd files render clean via
  mermaid-cli (first attempt needed a --no-sandbox puppeteer config since the
  sandbox runs as root). ER diagram visually inspected; system diagram SVG
  node/edge/label text inspected. GitHub will render the README embeds live.

## 2026-09-24 — U-1 alignment improvement (re-measured)
- Gold set `eval/ylt_gold.tsv`: 30 hand-aligned verses (Gen 1:1–12, Ps 23:1–6,
  Isa 53:1–12), 335 Hebrew words, 770 expected pairs; validated 0 errors.
- `build_ylt_align.py --eval`: baseline precision 0.6911 / recall 0.4766;
  anchored bridge precision 0.7941 / recall 0.4506; propagated variant tied
  (0.7941 / 0.4506) with zero propagated predictions on the gold set.
- Winner re-run over all 23,006 verses (exit 0): 337,601 `ylt_renderings` rows;
  propagation fired 0 times corpus-wide, so every row is labeled `bridged`
  (the shipped table is the anchored bridge).
- H3068 divine-name check on the gold set: 0 drift pairs under the anchored
  bridge (baseline: 1). Misses remain (recall gaps, not mis-maps).
- Honest re-measurement (`measure_ylt_coverage.py`): 325,284/575,877 YLT tokens
  mapped (56.4850%); 171,065/252,495 Hebrew words hit (67.7499%); per-book hit
  41.25% (Psalms) – 77.81% (Ezra); 81,430 misses, 5,718 = 7.0220% unbridgeable
  by Strong's; 60.6875% of hit words map to >1 distinct YLT word.
- `lexicon.ylt_renderings_computed` rebuilt via build_roots3.py →
  build_lexicon.py → build_lexicon_ylt.py: 95,967/126,869 rows (75.6426%).
- Website label "Young's (computed)" unchanged (drop-down + word detail page).
  Corpus stays READ-ONLY. Status: COMPUTED best-effort, NOT authoritative.

## 2026-09-25 — U-7 affix display normalization (closed)
- `normalize_affixes.py` (new, in project root): maps English affix glosses to
  Hebrew letters into NEW display columns `prefix1_disp`/`prefix2_disp`/
  `prefix3_disp`/`suffix1_disp`/`suffix2_disp` on `words` (ALTER TABLE + UPDATE;
  raw columns never overwritten). Backup `bible.db.bak-20260925-u7` (264,217 rows).
- 113,423 gloss occurrences normalized across 107,922/264,217 word rows:
  and,but→ו 51,210; to,for→ל 19,404; The,?→ה 16,454; in,with,by→ב 15,299;
  from→מ 6,346; as,like→כ 2,945; the,?→ה 1,633; that,which,who,whom→ש 132.
  'The, ?'/'the, ?'→ה resolved per-row (18,087/18,087 have ה at the expected
  position). Already-Hebrew values (maqqef-joined את-ה, כל-ה, …) pass through;
  suffix1/suffix2 held no English values.
- Verification (`verify_u7.py`, run log + mapping table kept in the workflow
  work dir): disp prefix chain is a literal prefix of word_unpointed
  113,671/113,673; disp suffix chain a literal suffix 44,274/44,276; zero
  Latin-looking values in disp columns; DISTINCT root_code 126,869 before and
  after; raw affix columns byte-identical to the backup. The 4 positional misses
  are pre-existing raw-parse quirks faithfully mirrored in disp (2× עד-למרחוק
  raw prefix1='from'; תיראומ raw suffix1='נ' vs ם ending; בתוכ-העמ raw
  suffix1='י' vs עמ ending) — display layer does not rewrite the parse.
- `bible.db` stays read-only for the website (contract unchanged).
- Follow-up (not done): word-detail template should read the `*_disp` columns
  — one-line template change.

## 2026-09-26 — U-8: KJV maqqef-component repair
- `kjv_renderings` gained a `method` column: `'direct'` for the 624,748
  original rows, `'maqqef-component'` for 2,281 new rows covering 810
  maqqef-split Hebrew words (KJV tokens matched via the OSHB-split
  sub-token Strong's). Words with ≥1 KJV rendering: 204,701 → 205,511
  (77.4746% → 77.7811%).
- Website impact: none needed — verse/word pages read `kjv_word` only;
  `lexicon.kjv_renderings` updated for the 712 affected root_vowel
  entries (687 went from empty to filled). `bible.db` stays read-only
  for the website (contract unchanged). Backup
  `bible.db.bak-20260926-u8-pre` kept.

## 2026-09-27 — U-9: KJV versification-offset repair
- 209 Hebrew references had zero same-reference `kjv_words` rows (MT-vs-KJV
  versification offsets, e.g. Gen 32:33 = KJV 32:32, Ex 7:26-29 = KJV 8:1-4,
  Joel 4 = KJV 3) — the U-8 diagnosis bucket (c). A verified 206-row
  verse-remap (`u9_verse_remap.tsv`, sequence-aware per-book alignment with
  Strong's-overlap gates and full-text adjudication of all 19 low-overlap
  picks) paired the 2,106 affected Strong's-carrying words against the remap
  target verse using the assembler's exact Strong's-sharing logic.
- 4,921 new `kjv_renderings` rows carry `method='verse-remap'` (existing rows
  never modified/deleted; all 569,740 pre-existing triples preserved). 1,801
  words repaired; 207,312/264,217 (78.4628%) now have a KJV rendering
  (was 205,511, 77.7811%). `lexicon.kjv_renderings` refreshed for 1,283
  affected cells. All 4,921 rows mechanically re-checked for Strong's
  sharing (bad=0). Limits: 305 words got no rendering (Strong's on no KJV
  word in target — same tagger-mismatch class as U-8's 45,582); three
  no-Strong's anomalous verses (Josh 4:32, Ruth 8:18, 2 Chr 36:32) left
  unrepaired by design.
- `bible.db` stays read-only for the website (contract unchanged); backup
  `bible.db.bak-20260927-u9-pre` kept.

## 2026-09-28 — U-7 follow-up: affix display row on word-detail page
- The website `/word/<wid>` page had no affix display; it now shows an
  "Affixes" row reading the normalized U-7 `*_disp` columns on `words`
  (`prefix1_disp`..`prefix3_disp`, `suffix1_disp`..`suffix2_disp`).
- Format: `prefix: <hebrew letters> / suffix: <hebrew letters>`, empty
  slots omitted, `(none)` when all five disp columns are empty. Raw
  affix columns (`prefix1` holding "and, but" etc.) are untouched and
  never displayed.
- Website impact: `website/app.py` `word_detail` only; no DB schema
  change, no writes — `bible.db` stays read-only for the website
  (contract unchanged).
- Verified live (port 5057): word 6 (raw prefix1='and, but') shows
  `prefix: ו` with no English gloss leak; word 2 (all disp empty) shows
  `(none)`; /word/6, /word/2, /verse/1/1/1, / all return 200.
  `bible.db` byte-identical afterward (md5
  9570752fc6f83b44dc5865923207fa73).

## 2026-09-28 — v2 normalization + laptop staging (proving ground)

- Kit: "the Bible project database is nowhere near normalized — it is glorified spreadsheet at this point." He authorized building a normalized replacement from the existing diagrams, with the laptop deploy as the proving ground. He has not reviewed/approved the specific schema (`schema_v2.md` says so explicitly).
- `schema_v2.sql` + `migrate_v2.py` → `bible_v2.db` (264,217 words, 66.9 s): lexicon blobs → 4 ordered child tables; morphology → `morph_patterns`/`morph_segments`; Strong's composites → `strongs` + `strongs_components` (reconstruction assertion 1,865/1,865); Strong's source → entity; `*_disp` → `root_form`; `verses(verse_id)` entity. `v_words` compat view 0 differing rows; 0 FK violations; lexicon round-trips 0 mismatches.
- `website/app_v2.py` (env: APP_DB, BIBLE_DB, USER_DIR, PORT, SCRIPT_NAME): 13/13 routes byte-identical to v1 locally; Python 3.10 f-string fixes for the laptop.
- Laptop staging (`/opt/bible`): `bible_v2.db` bit-identical (SHA-256 `4cacd562…e579e282`); supervisord `bible-v2` on 127.0.0.1:5058; Apache `/bible-v2` before `/bible`; separate app DB + choice dir. Verified: 13/13 internal 200s, 7/7 in-distro proxy 200s, live `/bible` regression 200s, full write path + cleanup. Distro rebooted ~1 h later; both programs self-recovered, health re-verified. Direct external access from this VM not reachable — no external claim. Live `app.py` + v1 `bible.db` untouched at that point (pre-cutover state).

## 2026-09-28 — live cutover (evening, ~17:15 PDT)

- Kit: "go live with it both on github and on the laptop." Cutover DONE.
- Laptop (`/opt/bible`): fresh pre-change backups in `backups/pre-cutover-2026-09-28/` (`bible.db` hash-verified, `app.db`, `app.py`, supervisor + Apache confs) + `ROLLBACK.txt`. Final `bible_v2.db` (384 MB) shipped gzipped (124 MB), unpacked and hash-verified bit-identical, moved in atomically; `app_v2.py` was already bit-identical.
- Supervisor `[program:bible]` now runs `app_v2.py` on port 5057 with `BIBLE_DB=/opt/bible/bible_v2.db`, `APP_DB=/opt/bible/website/app.db` (live user data; 0 translations at cutover), `SCRIPT_NAME=/bible`; Apache `/bible`→5057 unchanged.
- Verified: `/bible` + direct 5057 return 200; word/book/verse pages 200; live DB counts match local (words 264,217; alignment 836,290; word_variants 528,565; morph_variants 28; ATr words 171); corrected word page 150820 renders ATr. Both services RUNNING.
