# Bible Project — Notation Ledger

Living record of the project's shared vocabulary: Hebrew text notation,
morphology conventions, book/verse keying, translation-source labels, key
paths, and source pins. When a value changes, the old row is updated in
place with a dated note — this file always shows the current truth.
Unresolved items are `U-` numbered at the bottom.

## 1. Project terms

| Term | Meaning |
|---|---|
| Bible project | Kit's Hebrew Bible database + build-your-own-translation website (started 2026-09-20). |
| bible.db | SQLite database at `~/workspace/bible-project/bible.db` (build in progress, 2026-09-20). |
| Word | One row = one Hebrew/Aramaic token with book/chapter/verse/position. 264,217 rows across the Tanakh. |
| Pointed | `Word` column: Hebrew with vowel points and cantillation marks (e.g. בְּרֵאשִׁית). |
| Unpointed | `No_Vowel` column: consonantal text only (e.g. בראשית). The dropdown lists scholarly renderings of THIS form. |
| Slash-join | Prophets.ods convention: morphemes joined with `/` in the unpointed form (e.g. `ו/ה/מלכ` = prefix ו + prefix ה + base מלכ). |
| Strong's number | H-prefix index (H1–H8674) linking a Hebrew word to lexicon entries. Kit's own prefilled numbers (2026-09-20 and earlier) were discarded as the system of record on 2026-09-21 at his direction; where they conflicted with OSHB (105 rows) the OSHB value now stands. 22 rows keep a Kit value only because OSHB has no number for those words. |
| Root number (root_code) | The project's own numbering, generated 2026-09-21, replacing Kit's old numbering entirely. Format `root.fix.vowel` (e.g. `19247.42.1`). Covers all 264,217 words. See §8. |
| KJV person | Kit's stated preference (2026-09-20): King James Version is his translation; NIV excluded from the project. |
| Public-domain only | Standing rule (2026-09-20): every ingested text must be public domain or freely licensed. No NIV, no HALOT. |

## 2. Hebrew notation conventions

| Column / symbol | Meaning | Example |
|---|---|---|
| `Word` | Pointed surface form | בְּרֵאשִׁית |
| `No_Vowel` | Unpointed consonantal form | בראשית |
| `Prefix1/2/3` | Proclitic prefixes, in order | בְּ = "in, with, by" |
| `Base_Word` | Lexical stem after stripping affixes | ראשית |
| `Suffix1/2` | Pronominal/verbal suffixes | כ = "your" |
| `Language = A` | Aramaic token (Daniel, Ezra), not Hebrew | אבוהי (Dan 5:2) |
| `Var` | Variant marker (column present, usage TBD) | — |
| Verse key | `Verses.ods` style: lowercase book code + chapter:verse | `is1:1` = Isaiah 1:1 |
| Book codes (Verses.ods) | is, je, ek, ho, jl, am, ob, jn, mi, na, hb, zp, hg, zc, ma, lm, da, ec, ca | ca = Canticles (Song of Solomon) |

## 3. Book numbering (canonical: Books sheet, BibleFull v1)

1 Genesis (בראשית) · 2 Exodus (שמות) · 3 Leviticus (ויקרא) · 4 Numbers (במדבר) ·
5 Deuteronomy (דברים) · 6 Joshua (יהושע) · 7 Judges (שופטים) · 8 Ruth (רות) ·
9 1 Samuel (שמואל א) · 10 2 Samuel (שמואל ב) · 11 1 Kings (מלכים א) ·
12 2 Kings (מלכים ב) · 13 1 Chronicles (דברי הימים א) · 14 2 Chronicles (דברי הימים ב) ·
15 Ezra (עזרא) · 16 Nehemiah (נחמיה) · 17 Esther (אסתר) · 18 Job (איוב) ·
19 Psalms (תהלים) · 20 Proverbs (משלי) · 21 Ecclesiastes (קהלת) ·
22 Song of Solomon (שיר השירים) · 23 Isaiah (ישעיה) · 24 Jeremiah (ירמיה) ·
25 Lamentations (איכה) · 26 Ezekiel (יחזקאל) · 27 Daniel (דניאל) · 28 Hosea (הושע) ·
29 Joel (יואל) · 30 Amos (עמוס) · 31 Obadiah (עבדיה) · 32 Jonah (יונה) ·
33 Micah (מיכה) · 34 Nahum (נחום) · 35 Habakkuk (חבקוק) · 36 Zephaniah (צפניה) ·
37 Haggai (חגי) · 38 Zechariah (זכריה) · 39 Malachi (מלאכי)

## 4. Translation-source labels (website dropdowns)

| Label | Source | License | Granularity |
|---|---|---|---|
| KJV | King James Version + Strong's | Public domain | Word-level (via Strong's alignment) |
| YLT | Young's Literal Translation | Public domain | Verse-level; word-level best-effort |
| BDB | Brown-Driver-Briggs lexicon | Public domain | Per Strong's number (scholarly gloss list) |
| Strongs | Strong's Hebrew dictionary | Public domain | Per Strong's number (second gloss source) |

## 5. Key paths

| Path | Contents |
|---|---|
| `~/workspace/bible-project/` | Project root |
| `~/workspace/bible-project/NOTATION_LEDGER.md` | This file |
| `~/workspace/bible-project/bible.db` | SQLite database: built 2026-09-20 (264,217 words, OSHB crosswalk, KJV/YLT/glosses); root numbering added 2026-09-21. |
| `~/workspace/bible-project/BUILD_NOTES.md` | Never written by the builder; `assembly_report.json` + DB queries are the build record. |
| `~/workspace/bible-project/er_diagram.png` / `.svg` | Entity-relationship diagram (2026-09-20) |
| `~/workspace/bible-project/system_diagram.png` / `.svg` | System architecture diagram (2026-09-20) |
| `~/workspace/bible-project/er.py`, `sys.py` | Diagram generators (matplotlib) |
| `~/workspace/user/files/` | Kit's uploads: BibleFull (v 1).xlsx, Prophets.ods, Verses.ods |
| `/tmp/bible/` | xlsx conversions of the two .ods files (ephemeral) |

## 6. Source pins

| Source | Intended use | License | Status |
|---|---|---|---|
| OSHB / morphhb (Open Scriptures) | Hebrew text + Strong's + morphology; crosswalk target | CC BY | To be fetched |
| KJV + Strong's dataset | Word-level English renderings | Public domain | To be fetched (verify PD) |
| YLT (e.g. ebible.org eng-ylt) | Literal English verse text | Public domain | To be fetched |
| BDB (openscriptures HebrewLexicon) | Scholarly glosses per Strong's | Public domain | To be fetched |
| Strong's Hebrew dictionary | Second gloss source | Public domain | To be fetched |

## 8. Root numbering system (2026-09-21, replaces Kit's old numbering)

Three tiers. Syntax: **`root.fix.vowel`**.

1. **Root.** Every distinct **unpointed base word** is a root entry, numbered
   sequentially in Hebrew alphabetical order (`root_entry`: 30,087 roots,
   `root_id` 1–30087).
2. **Fix.** Beneath each root, every distinct **(prefix1, prefix2, prefix3,
   suffix1, suffix2)** combination attested in the text is a numbered form
   (`root_form`: 57,724 forms), ordered alphabetically by the affix tuple.
3. **Vowel.** Beneath each (root, form), every distinct **pointed (vocalized)
   form** attested in the text is a numbered vowel pattern (`root_vowel`:
   126,869 patterns), ordered by Unicode sort of the pointed string.

Each word carries `root_id`, `root_form_seq`, `root_vowel_seq`, and the display
code `root_code = root_id.root_form_seq.root_vowel_seq`.

- Example: root מלכ is **19247** (2,095 words). Form **19247.42** is ה+מלכ
  "the king" (770×); **19247.42.1** is its first vocalization pattern.
- Coverage is total by construction: all 264,217 words have a three-part
  root_code, including the 88,768 words the OSHB crosswalk could not reach.
  One word has an empty pointed form; it is the sole pattern of its group.
- Root 1 is the empty string: 7 paseq marks (׀, Exod 13 / Ezek 8) whose unpointed
  form is empty. Deterministic; left as-is.
- Note on the affix columns: they are Kit's own parsing and are uneven —
  `prefix1`/`prefix2` often hold an English gloss of the prefix ("and, but",
  "the, ?") rather than Hebrew letters, and `prefix3` sometimes holds a whole
  preceding maqqef-joined word ("אל-ה"). Grouping is still exact (identical
  tuples group together). U-7 display normalization landed 2026-09-25: new
  `*_disp` columns hold the Hebrew-letter forms (English glosses mapped,
  e.g. "and, but"→ו; raw columns untouched, so grouping is unaffected).
- Strong's numbers are retained as a foreign key into the public-domain
  lexicons (KJV/gloss dropdowns), but the root code is the project's primary
  word numbering.
- **Lexicon (2026-09-21).** New `lexicon` table, one row per ROOT_VOWEL entry
  (126,869 rows): `kjv_renderings` (distinct KJV words aligned to the form's
  word_ids, most frequent first, `|`-separated; word-level, 71,122 entries have
  at least one), `ylt_contexts` (the YLT verse texts for every verse where the
  form occurs, `Ref — text` entries separated by `‖`; YLT is verse-level in our
  sources, not a per-word gloss — 126,046 entries have at least one), and
  `found_verses` (the verse references, `;`-separated, canonical order).
  Builder: `build_lexicon.py`.

## 9. Website implementation (2026-09-22)

- Spec (Kit): drop-down over each Hebrew word — KJV rendering, Young's rendering
  (COMPUTED, labeled as such), Other (user-defined, the academic pass). Browse
  book → chapter → verse → words; choosing word by word builds and saves his
  translation.
- `website/schema.sql`: `app.db` holds `app_user`, `translation`,
  `other_option(option_id, translation_id, idx, text, created_at)` — the
  multi-value "Other" renderings. Per-word choices are NOT rows: each
  translation gets `website/user_data/translation_<id>.choices`, ONE BYTE PER
  WORD (264,217 bytes), byte at offset (word_id − 1). Byte = drop-down item
  number selected: 0 = default (no choice); rest index into the word's
  drop-down rebuilt identically as [KJV renderings | Young's-computed
  renderings | this translation's Other options] (Kit's spec, 2026-09-22).
  `bible.db` opened read-only; `word_id` is a logical cross-db reference
  enforced by application code. Note: byte meaning is per-word (item lists
  differ per word); if corpus renderings are ever recomputed, stored bytes
  may point at different items (stale bytes fall back to default).
- `website/app.py` (Flask, port 5057): `/` books; `/book/<n>` chapters;
  `/chapter/<n>/<c>` verses; `/verse/<n>/<c>/<v>` words with per-word
  KJV/Young's-computed/Other dropdown + save; `POST /choice`; `/translations`
  create/select; `/reading/<tid>/<n>/<c>/<v>`; `/export/<tid>` (text download);
  `/word/<wid>` detail (pointed/unpointed, letters, root code, Strong's, KJV/YLT
  renderings, lexicon contexts, found verses).
- Tested locally end-to-end 2026-09-22 (byte-file design): all routes 200;
  translation created; KJV item byte + new multi-value Other option saved;
  verified on disk (264,217-byte file, correct bytes at word offsets,
  `other_option` row); verse page re-renders selected items; reading view
  composes; export downloads. Test data removed (`app.db`, `user_data/`).
- Diagrams: `website/website_er.png`/`.svg`, `website/website_system.png`/`.svg`
  (builder `website_diagrams.py`); status log `website/STATUS.md` (read by the
  morning report).

## 10. Unresolved items

- **U-1** (2026-09-20): YLT word-level alignment — verse-level is certain; word-level is best-effort. Update 2026-09-21: verse-level confirmed in DB (`ylt_verses`, 23,145 rows). Update 2026-09-22: first computed word-level alignment (`build_ylt_align.py`, baseline KJV-bridge): `ylt_renderings(word_id, ylt_word, ylt_word_pos)`, 259,171 rows; 23,006 verses; 36.0% of YLT tokens mapped; 43.6% of Hebrew words hit; spot-checks showed real errors (H3068→"from"). Update 2026-09-24 (U-1 accuracy improvement): hand-aligned gold set `eval/ylt_gold.tsv` (30 verses — Gen 1:1–12, Ps 23:1–6, Isa 53:1–12; 335 Hebrew words, 770 expected pairs; validated against the DB, 0 integrity errors). `build_ylt_align.py --eval` scored three bridge methods (shared YLT↔KJV Needleman-Wunsch): baseline precision 0.6911 / recall 0.4766; **anchored** (one-to-one exact-Strong's anchors + position-capped gap-fill) precision **0.7941** / recall 0.4506; propagated (root-family propagation for blank-Strong's words) precision 0.7941 / recall 0.4506 with zero propagated predictions on the gold set — and zero propagated rows on the full corpus, so the shipped table is the anchored bridge. Winner re-run over all 23,006 verses (exit 0): `ylt_renderings(word_id, ylt_word, ylt_word_pos, label)`, 337,601 rows, all labeled `bridged`. H3068 divine-name check on the gold set: zero drift pairs under the anchored bridge (the baseline attached 1 wrong YLT token to an H3068 word); H3068 misses remain (e.g. Ps 23:1 יְהוָה unmapped) — recall gaps, not mis-maps. Coverage re-measured honestly (`measure_ylt_coverage.py`, exact numerators/denominators; the corpus-coverage gains since 2026-09-22 combine the OSHB crosswalk's Strong's fill with the new bridge — the bridge improvement itself is established on the gold set: precision 0.6911 → 0.7941, H3068 drift 1 → 0): 325,284 / 575,877 YLT tokens mapped = 56.4850%; 171,065 / 252,495 Hebrew words with ≥1 YLT row = 67.7499% (of 264,217 words in db); per-book hit 41.25% (Psalms) – 77.81% (Ezra); 81,430 misses, of which 5,718 = 7.0220% unbridgeable by Strong's (blank Strong's; was 59.2% before the crosswalk); 103,815 / 171,065 = 60.6875% of hit words map to >1 distinct YLT word. Status: COMPUTED best-effort, NOT authoritative (unchanged). Lexicon carries it as `ylt_renderings_computed` (95,967/126,869 rows = 75.6426%), labeled "Young's (computed)" in the website UI. Closed 2026-09-24: accuracy improvement complete — anchored bridge shipped (337,601 rows, all labeled `bridged`); gold-set precision 0.6911 → 0.7941, H3068 drift 1 → 0; honest coverage numbers re-measured and recorded above. The alignment itself stays COMPUTED best-effort, NOT authoritative; a future re-alignment would open a new item.
- **U-2** (2026-09-20): Prophets.ods Psalms sheet (62 cols, stray `]צ`, trailing numbers) and Hosea sheet (1024 cols, stray values) contain junk columns. Closed 2026-09-21: extra columns ignored as junk in the ingest (canon_report.json); Prophets sheets matched the canonical list at 99.85%.
- **U-3** (2026-09-20): Canonical word source undecided — BibleFull's Bible sheet vs Prophets.ods per-book sheets. Closed 2026-09-21: BibleFull's Bible sheet is canonical (264,217 rows); Prophets.ods used as a check.
- **U-4** (2026-09-20): `Var` and `Notes` columns in the notes sheet have no documented meaning yet. Kit to define, or drop.
- **U-5** (2026-09-20): "Green literal translation" read as Young's Literal Translation; Kit confirmed the plan containing YLT on 2026-09-20. Closed unless corrected.
- **U-6** (2026-09-20): Website stack and hosting undecided. Flask + SQLite is the working assumption; Kit hasn't chosen.
- **U-7** (2026-09-21): Affix columns are Kit's own uneven parsing — `prefix1`/`prefix2` often hold English glosses ("and, but") instead of Hebrew letters, and `prefix3` sometimes holds a whole preceding maqqef-joined word ("אל-ה"). The root numbering groups on these tuples exactly, so numbering is unaffected, but a future pass should normalize them to Hebrew letters for display. **Closed 2026-09-25:** display pass complete via `normalize_affixes.py` — new columns `prefix1_disp`/`prefix2_disp`/`prefix3_disp`/`suffix1_disp`/`suffix2_disp` on `words` (raw columns untouched; backup `bible.db.bak-20260925-u7`). 113,423 gloss occurrences normalized across 107,922/264,217 word rows: and,but→ו (51,210), to,for→ל (19,404), The,?→ה (16,454), in,with,by→ב (15,299), from→מ (6,346), as,like→כ (2,945), the,?→ה (1,633), that,which,who,whom→ש (132); the ה mappings verified per-row positionally 18,087/18,087. Already-Hebrew values (incl. maqqef-joined את-ה etc.) pass through unchanged; suffix1/suffix2 held no English values. Verification (`verify_u7.py`, exact numerators/denominators): disp prefix chain is a literal prefix of word_unpointed 113,671/113,673; disp suffix chain a literal suffix 44,274/44,276; zero Latin-looking values in disp columns; DISTINCT root_code 126,869 before and after; raw affix columns byte-identical to backup. The 4 positional misses are pre-existing raw-parse quirks faithfully mirrored in disp (2× עד-למרחוק raw prefix1='from'; תיראומ raw suffix1='נ' vs ם ending; בתוכ-העמ raw suffix1='י' vs עמ ending) — the display layer does not rewrite Kit's parse. Follow-up (was: not done): website word-detail template should read the `*_disp` columns. **Closed 2026-09-28:** `website/app.py` `word_detail` now shows an "Affixes" row reading the normalized `*_disp` columns (prefix: ו / suffix: ך, empty ones omitted, '(none)' when all empty; raw columns untouched, DB read-only). Verified live on port 5057: word 6 (raw prefix1='and, but') shows `prefix: ו` with no English gloss leak; word 2 (all disp empty) shows `(none)`; /word/6, /word/2, /verse/1/1/1, / return 200; `bible.db` byte-identical afterward (md5 9570752fc6f83b44dc5865923207fa73).`
- **U-9** (2026-09-27): KJV versification-offset gap — the U-8 diagnosis bucket (c): 2,106 Strong's-carrying words in verses missing from the KJV dataset. **Diagnosis** (workflow workdir `u9_diagnose.py`, `u9_verse_gaps.json`): 209 Hebrew references have zero same-reference `kjv_words` rows; those verses hold 2,155 words, 2,106 with Strong's. Three anomalous verses have words but zero Strong's (Josh 4:32, Ruth 8:18, 2 Chr 36:32) — unrepairable by Strong's pairing, left alone. **Verse-remap** (`u9_remap2.py` → verified `u9_verse_remap.tsv`, 206 rows): sequence-aware alignment — per-book KJV ordinals, gap verses grouped into contiguous runs, each run mapped to a consecutive KJV sequence maximizing distinct-Strong's overlap (>0.5 required per verse) with order tiebreaks resolved by run-majority then book-majority offset (never by arbitrary insertion order). Formulaic ties (e.g. "the LORD spoke to Moses" verses) resolved by sequence: Num 17:14–28 → KJV 16:49,16:50,17:1–13; Lev 5:20–26 → KJV 6:1–7. **Spot-check gate** (`u9_spotcheck.py` dossier + `u9_adjudication.md`): all 19 queued remaps (overlap <0.70, anchors Gen 32:33→KJV 32:32 and Ex 7:26–29→KJV 8:1–4, tiebreak/regional-carry basis) adjudicated by reading full Hebrew vs KJV verse text — all 19 correct; plus 5 tiebreak picks text-verified (Num 17:16→17:1, Ps 8:10→8:9, 42:12→42:11, 46:12→46:11, 57:12→57:11). Per-book offset audit matches documented MT-vs-KJV versification (Joel 4→3 ×21, Mal 3:19–24→4:1–6, 1 Chr 5:27–41→6:1–15, Dan 3:31–33→4:1–3, Ezek 21:33–37→21:28–32, etc.). **Canon-quirk discovery**: Kit's source relocates verse 1 to the chapter end under a bogus number for Isa 27 ("27:22"), Jer 28 ("28:23"), Lam 2 ("2:23") — same pattern as Ps 17:17 and the assembler's existing VERSE_REMAP; verses 2..N align normally, the remap pairs the relocated verse to KJV v1 by text. **Repair** (`repair_u9_verse_remap_kjv.py`, documented builder script, `--db`/`--remap`/`--limit`/`--dry-run`): pairs each word in the 206 remapped verses against the remap target verse with the assembler's exact normalized Strong's-sharing logic (`w['strongs'] in set(multi_strongs(kjv_strongs))`); `kjv_strongs` stored as the normalized set comma-joined (sorted for determinism; the assembler joined the same set in arbitrary order). Existing rows never modified/deleted; new rows carry `method='verse-remap'`; (word_id, kjv_word) pairs already present are skipped. Slice-tested on a copy (3 verses: 86 rows, 0 existing-collisions) before the full run. Backup `bible.db.bak-20260927-u9-pre` kept. **Verification** (`verify_u9.py`, exact checks): all 10 non-`kjv_renderings` tables byte-identical after the rendering repair; every pre-existing (word_id,kjv_word,kjv_strongs) triple preserved (569,740/569,740); 4,921 new rows all method='verse-remap', zero colliding with existing pairs; all 4,921 rows mechanically re-checked for Strong's sharing (bad=0); 206 repaired verses; 18 verse-remap rows spot-checked against the source KJV+Strong's text (all correct, e.g. לא־יֹאכְלוּ H398 → "eat" H0398 in KJV Gen 32:32). **Lexicon** (`repair_u9_lexicon.py`, same cell computation as `build_lexicon.py`): 1,635 affected groups, 1,283 `kjv_renderings` cells updated (836 empty→filled), all other lexicon fields/rows byte-identical; every changed cell re-verified against a from-scratch recomputation (1,283/1,283 match). **Result**: 1,801 words repaired (+4,921 rows): 207,312/264,217 words with ≥1 KJV rendering = 78.4628% (was 77.7811%); of Strong's-carrying words 207,312/258,209 = 80.2884% (was 79.5910%). **Limits**: 305 gap words got no rendering — their Strong's appears on no KJV word in the remap target (same tagger-mismatch class as U-8's 45,582); 46 words have no Strong's; the three no-Strong's anomalous verses remain unrepaired by design. YLT computed/best-effort labels unchanged; website still opens `bible.db` read-only (`mode=ro`).
- **U-8** (2026-09-26): KJV word-rendering coverage gap — 258,209/264,217 words carry Strong's but only 204,701 (77.4746%) had a KJV rendering. **Diagnosis** (`u8_diagnosis.json`, workflow work dir): the 53,508-word gap buckets as (a) 4,945 maqqef-split words (strongs_source='oshb-split') — REPAIRED; (b) 45,582 words whose Strong's appears on no KJV word in the verse — the KJV+Strong's source tags those English words with a different Strong's or leaves them untagged (phrase-level tagging, e.g. "Let there be" all tagged H7549, H1961 unrepresented) — NOT repairable without guessing; (c) 2,106 words in verses missing from the KJV dataset (versification offsets, e.g. Gen 32:33 = KJV 32:32) — needs a verified verse-remap, a separate item; (d) 875 Aramaic words — same implicit-rendering class as (b). **Repair** (`repair_u8_maqqef_kjv.py`, documented builder script): for maqqef-split words with Strong's but zero renderings, propagate KJV tokens matched via the OSHB-split sub-token Strong's alignments (the crosswalk's own pairings, re-run verbatim from assemble_bible.py against the same oshb_words.tsv) to the parent word_id. Existing kjv_renderings rows never modified/deleted; new rows carry `method='maqqef-component'` (existing 624,748 rows backfilled `method='direct'`) so the table stays honest. Worked on a copy; backup `bible.db.bak-20260926-u8-pre` kept. **Verification** (`u8_verify2.py`, exact SQL EXCEPT row-multiset comparison): all 10 other tables byte-identical to pristine; every pre-existing (word_id, kjv_word, kjv_strongs) triple preserved (missing=0 extra=0); zero maqqef-component rows collide with existing pairs; zero words lost renderings. 15 repaired words spot-checked against the source KJV+Strong's text — all attachments correct (e.g. אֲכָל־מִמֶּנּוּ → "Hast/thou/eaten/eat" via H398 אכל; הַכּוֹת־אֹתוֹ → "him/should/kill" via H5221 נכה). **Result**: 810 words repaired (+2,281 rows): 205,511/264,217 words with ≥1 KJV rendering = 77.7811% (was 77.4746%); of Strong's-carrying words 205,511/258,209 = 79.5910% (was 79.2773%). 4,421 maqqef gap words remain unrepaired — their sub-token Strong's appears on no KJV word in the verse (KJV taggers left those English words untagged, e.g. "was" in "and it was so"). `lexicon.kjv_renderings` rebuilt for the 712 affected root_vowel entries (`repair_u8_lexicon.py`, same cell computation as build_lexicon.py; other lexicon columns/rows untouched; 687 entries went from empty to filled; lexicon rows with KJV renderings 111,072 → 111,759). Status: alignment repair, NOT a new authoritative alignment — the maqqef-component rows are labeled as such in the table. **U-7 template follow-up NOT done**: the website word-detail page has no affix display at all, so the "one-line change to read *_disp" has no target — adding one would be a new UI row, out of scope.
- **Anomaly resolutions applied (2026-09-29)**: `anomaly_resolutions.json` held 129 OSHB-verbatim-evidenced corrections for corrupt `words.unpointed`/`letters` (108 truncation-at-maqaf, 20 wrong-row-data, 1 token-split-misalignment; 128 high / 1 medium confidence, 0 unresolved) — researched and staged in `word_variants` (seq 1 v1-stored, seq 2/3 resolved) but never applied to the primary columns, which feed root numbering, lexicon grouping, and website display. **Applied** (`apply_anomaly_resolutions.py`, documented builder script, `--db`/`--dry-run`/`--limit`, idempotent): the 128 high-confidence word_ids got `unpointed`/`letters` := the `_v1conv` forms (v1-medial/hyphen-minus column convention preserved per the file's `_meta` note); the 1 medium-confidence record (word 104753, 'ככ'→'כי־על') stays variants-only. Of the 128, 127 needed the UPDATE (word 71448's value was already correct — the documented token-split artifact row, empty pointed by design). **Root re-derivation** (same grouping rules as `build_roots2.py`/`build_roots3.py`: corrected unpointed form = root key; affix tuple carried over unchanged; vowel tier keys on the unchanged pointed): 127 words re-pointed, 1 (word 84266, 'לכק'→'לכ') kept its existing assignment — only its surface columns were corrupt. Existing IDs fixed, no renumbering; appended 62 `root_entry`, 92 `root_form`, 97 `root_vowel` rows (max root_id 30,087 → 30,149); 77 old roots left at word_count 0 and logged (incl. junk roots 'קק'; 'ככ' retains 1 word = the medium-confidence 104753). Wrong-row-data words merged into real roots (e.g. 'ככ'→'בני' root 6627, 'ככ'→'אלי', 'ככ'→'צבאות', 'קק'→'יסלח-נא', 'זאת]צ'→'זאת'). Slice-tested on a copy (`--limit 5`) before the full run. Backup `bible_v2.db.bak-20260929-anom` (SHA-256 `0eaaf38f…b03ff`) kept; new `bible_v2.db` SHA-256 `172fc313…6eb98bad`. **Lexicon**: 235 touched root_vowel groups rebuilt with the exact `build_lexicon.py`/`build_lexicon_ylt.py` cell computations (kjv 112, ylt 82, ylt_contexts 226, found_verses 226 cells rewritten; touched rows only). **Verification** (`verify_anomaly.py`, exact SQL row-multiset comparison vs pristine, 31 checks, all pass): all 14 other tables 0 diffs both ways; `words` 264,217 rows, id set unchanged, exactly the 128 word_ids differ and only in (unpointed, letters, root_id, root_form_seq, root_vowel_seq) with values == resolved; 0 FK violations; root word_counts reconcile to 264,217; all 235 touched lexicon groups match a from-scratch recomputation; every applied value mechanically re-checked against its OSHB evidence (128/128: applied == desofit(maqaf-joined evidence tokens)); the `migrate_v2.py` candidate-derivation rule reproduces the applied values 127/127 + 1 documented (71448, empty pointed); re-run is a no-op (byte-identical SHA-256). Website: 6/6 sampled `/word/<wid>` pages return 200 and render the corrected unpointed/letters (51400, 84702, 126741, 71447, 84266, 104753-unchanged); `bible_v2.db` still opened read-only (`mode=ro`, contract unchanged). YLT 'computed' honesty labels unchanged. Laptop ship left to the deploy stage.

## 11. Normalization (v2, 2026-09-28)

- Kit's directive: "the Bible project database is nowhere near normalized — it is glorified spreadsheet at this point." He authorized building a normalized replacement from the existing DFD, ER, and context diagrams, with the laptop deploy as the proving ground. Kit approved the schema 2026-09-28 ("the schema looks great"; `schema_v2.md`).
- **Design** (`schema_v2.md`, `schema_v2.sql`): every multi-value TEXT blob decomposed into ordered child tables, every lookup its own entity. Changes: lexicon → header + 4 `seq`-ordered child tables (`lexicon_kjv_rendering`, `lexicon_ylt_rendering`, `lexicon_ylt_context`, `lexicon_found_verse`); morphology string → `morph_patterns` + `morph_segments` (parsed per the pinned OSHB morphhb code rules); Strong's composites → `strongs` entity (exact raw string preserved) + `strongs_components` (ordered verbatim components); Strong's source free text → `strongs_sources` entity; `*_disp` affix columns moved `words` → `root_form` (0 FD violations); `(book, chapter, verse)` → `verses(verse_id)` entity. `word_id` stable (choice-file contract). `orig_word_id` NOT unique in v1 (3 source ids — 51399, 252785, 227963 — each map to 2 rows via split/merged tokens); kept as a plain import key, no UNIQUE constraint.
- **Attribution**: WLC Hebrew text is public domain; OSHB lemma/morphology annotations are CC BY 4.0 (recorded in `schema_v2.md` §4 and DFD entity "OSHB / morphhb").
- **Migration** (`migrate_v2.py`, 66.9 s): 264,217 words; `v_words` compatibility view 264,217 rows, 0 differing; 0 FK violations; 79 null morphology assignments (matches v1); KJV/YLT lexicon child round-trips 0 mismatches on 126,869 rows; 3,437 morphology patterns, 7,552 parsed segments, 1 unparsed (`AT` — bare `T` on Aramaic דִּי in Daniel has no documented particle type; 5 occurrences); 19,058 distinct raw Strong's, 1,865 composites → 3,783 ordered component rows; Strong's reconstruction assertion (components re-joined in `seq` order must equal the raw string) — 1,865/1,865 pass; 155 component strings have no standalone `strongs` row (recorded, not forced). `unpointed`/`letters` copied verbatim; 129 candidate-derivation disagreements logged in `unpointed_letters_anomalies.json`, never applied (the earlier count of 208 was superseded — its code was not retained).
- **App** (`website/app_v2.py`): env-configured (`APP_DB`, `BIBLE_DB`, `USER_DIR`, `PORT`, `SCRIPT_NAME`); reads the v2 columns directly. 13 routes byte-identical to v1 locally (incl. byte-identical choice files and export); Python 3.10 f-string corrections required for the laptop (no nested quotes/backslashes in f-string expressions). Live `app.py`/`bible.db` untouched at this point — **cutover DONE 2026-09-28 ~17:15 PDT** (see Status below).
- **Staging** (laptop, `/opt/bible`): `bible_v2.db` bit-identical (SHA-256 `4cacd562…e579e282`); supervisord `bible-v2` on 127.0.0.1:5058; Apache `/bible-v2` (inserted before `/bible`); separate app DB + choice dir; `SCRIPT_NAME=/bible-v2`. 13 routes 200 on the internal port; 7 routes 200 through the in-distro Apache proxy; live `/bible` regression 200s. Write path verified (translation create, choice POST, 264,217-byte choice file, reading view, 69,647-line export) and cleaned up. Direct external access from this VM to the laptop was not reachable (curl 000/52), so no external claim is made. A failed first write-test run left staging-test rows (IDs 1 and 2) — both verified as test artifacts and removed 2026-09-28 along with `translation_2.choices`; the staging translation table is empty.
- **Diagrams** (`er_v2.py`, `dfd_v2.py`, `context_v2.py`): semantic review 2026-09-28 caught and fixed two ER errors — WORDS→STRONGS_SOURCES markers were inverted (now N-1) and LEXICON_YLT_CONTEXT pointed at YLT_VERSES instead of its actual FK target `verses`; DFD made the v1 corpus explicit (`bible.db (v1)` flow p1→p2) and un-swapped the user↔serve HTTP/pages arrows; context dropped a dangling "translation choices" from the builder box. All FK directions verified against `schema_v2.sql` DDL. Not drawn by design: `words.root_id`→`root_entry` direct FK (represented via the composite FK to `root_vowel` + the drawn ROOT_ENTRY→ROOT_FORM→ROOT_VOWEL chain) and the secondary `kjv_words.strongs`/`kjv_renderings.kjv_strongs` alignment keys.
- **Status**: **live cutover DONE 2026-09-28 ~17:15 PDT** (Kit: "go live with it both on github and on the laptop"). Supervisor `bible` runs `app_v2.py` on port 5057 against `bible_v2.db`; pre-change backups + ROLLBACK.txt in `/opt/bible/backups/pre-cutover-2026-09-28/`. The v1 corpus and app are preserved in the pre-cutover backup for the record.
