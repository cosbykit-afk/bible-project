# Bible Project

A Hebrew Bible database and build-your-own-translation website. Every
unpointed Hebrew word gets a dropdown of academically sourced renderings;
readers pick word by word and save their own translation.

**Public-domain sources only.** No NIV, no HALOT.

## What's here

| File | Purpose |
|---|---|
| `NOTATION_LEDGER.md` | Living record: Hebrew notation conventions, book numbering, source labels, open items |
| `er_diagram.png` / `.svg` | Entity-relationship diagram |
| `system_diagram.png` / `.svg` | System architecture diagram |
| `er.py`, `sys.py` | Diagram generators (matplotlib) |
| `ingest_canonical.py` | Ingests Kit's spreadsheets, picks the canonical word list |
| `assemble_bible.py` | Full assembly: crosswalk to OSHB, KJV/YLT/gloss loading, SQLite build |
| `fixup_notes.py`, `diff_corrected.py` | One-off cleaning passes |
| `oshb_crosswalk_report.json` | OSHB alignment statistics |
| `assembly_report.json` | Final build verification numbers |
| `spotcheck.txt` | Human-readable verse samples |

## The database (built 2026-09-20)

`bible.db` (SQLite, git-ignored — rebuild with `assemble_bible.py`):

| Table | Rows | Notes |
|---|---|---|
| `words` | 264,217 | One row per Hebrew/Aramaic token; morphology parsed; Strong's via OSHB crosswalk |
| `kjv_renderings` | 631,950 | KJV word renderings aligned to Hebrew words |
| `kjv_words` | 610,324 | Raw KJV+Strong's word list |
| `ylt_verses` | 23,145 | Young's Literal Translation, verse level |
| `ylt_renderings` | 337,601 | YLT word ↔ Hebrew alignment (COMPUTED best-effort, U-1) |
| `glosses` | 17,347 | BDB + Strong's dictionary glosses, full H1–H8674 |
| `books` | 39 | English + Hebrew names |
| `root_entry` | 30,087 | The project's own numbering: one row per distinct unpointed base word, Hebrew alphabetical order |
| `root_form` | 57,724 | Numbered prefix/suffix patterns beneath each root |
| `root_vowel` | 126,869 | Numbered pointed (vocalized) forms beneath each (root, form); `words.root_code` = `root.fix.vowel` |
| `lexicon` | 126,869 | One row per `root_vowel` entry: KJV renderings (word-level, most frequent first), YLT verse contexts (verse-level), and the verse list where the form is found |

**Numbering.** The project's primary word numbering is root-based (built
2026-09-21, replacing Kit's earlier numbering), in three tiers: every distinct
unpointed base word is a numbered root entry, each attested prefix/suffix
pattern beneath it is a numbered form, and each distinct pointed (vocalized)
form beneath that is a numbered vowel pattern. Every one of the 264,217 words
carries a `root_code` like `19247.42.1` (root מלכ, "the king" form, first
vocalization). Strong's numbers are kept as a foreign key into the
public-domain lexicons.

Coverage: 258,209 of 264,217 words carry a Strong's number (97.7261%),
every one of those has at least one gloss. 207,312 words (78.4628%) have a
KJV rendering — raised from 205,511 (77.7811%) by the U-9 verse-remap repair
(2026-09-27): 1,801 words in 206 verses with MT-vs-KJV versification offsets
(e.g. Gen 32:33 = KJV 32:32, Ex 7:26–29 = KJV 8:1–4, Joel 4 = KJV 3) gained
renderings by pairing against the verified remap target verse with the same
normalized Strong's-sharing logic as the original alignment; the 4,921 new
`kjv_renderings` rows are labeled `method='verse-remap'` (earlier rows are
`method='direct'` / `method='maqqef-component'`). The U-8 maqqef-component
repair (2026-09-26) had raised coverage from 204,701 (77.4746%).
4,405 Aramaic words flagged. Strong's coverage rose via the OSHB
crosswalk (2026-09-24); the remaining KJV gap is a source limitation, not a
crosswalk bug — the KJV+Strong's dataset tags many English words with a
different Strong's than the Hebrew word's, or leaves them untagged
(phrase-level tagging); 2,106 further words sit in verses missing from the
KJV dataset under versification offsets (e.g. Gen 32:33 = KJV 32:32) —
see `oshb_crosswalk_report.json` and NOTATION_LEDGER.md U-8.

## Sources (all public domain / freely licensed)

- Kit's spreadsheets: BibleFull (v 1).xlsx, Prophets.ods, Verses.ods
- OSHB / morphhb (Open Scriptures Hebrew Bible) — Hebrew text + Strong's + morphology
- KJV + Strong's (Crosswire)
- Young's Literal Translation (ebible.org eng-ylt, USFM)
- BDB + Strong's Hebrew dictionary (Open Scriptures HebrewLexicon)

## Status

Database built; website built and tested locally (2026-09-22). Open items are tracked as `U-`
items in `NOTATION_LEDGER.md`.

### v2 normalization (2026-09-28, implementation draft under Kit's authorization)

`schema_v2.md` (design) + `schema_v2.sql` (DDL) + `migrate_v2.py` (migration, 66.9 s)
rebuild the corpus as a normalized database: every multi-value TEXT blob is
decomposed into ordered child tables, every lookup list is its own entity.

| Change | Before (v1) | After (v2) |
|---|---|---|
| Lexicon blobs | `lexicon` held 4 multi-value TEXT columns (`kjv_renderings`, `ylt_renderings`, `ylt_contexts`, `found_verses`) | `lexicon` header + `lexicon_kjv_rendering`, `lexicon_ylt_rendering`, `lexicon_ylt_context`, `lexicon_found_verse` (all `seq`-ordered; exact round-trip verified, 0 mismatches on 126,869 rows) |
| Morphology | one opaque `morphology` string per word (3,437 distinct patterns) | `morph_patterns` + `morph_segments` (7,552 parsed segment rows; OSHB morphhb code rules; `AT` on Aramaic די left `unparsed` — bare `T` has no documented type) |
| Strong's | comma-joined composites like `H01,H015` inside one column | `strongs` entity keeps the exact raw string; `strongs_components` stores the ordered verbatim components (3,783 rows from 1,865 composites) |
| Strong's source | free-text column (`oshb`, `oshb-split`, `kit`, blank) | `strongs_sources` entity, FK-checked (`CHECK (strongs IS NULL) = (strongs_source_id IS NULL)`) |
| Affix display | `*_disp` columns on `words` (transitively dependent on the form) | moved to `root_form` (FD-verified against the build) |
| Verse identity | `(book_num, chapter, verse)` repeated everywhere | `verses(verse_id)` entity; `words.verse_id` FK |
| `orig_word_id` | assumed unique | NOT unique in v1 (3 source ids each map to 2 rows: split/merged tokens 51399, 252785, 227963); kept as a plain import key with an index |

`word_id` is stable (required by the one-byte choice files). `unpointed`/`letters`
are preserved verbatim from v1; 129 candidate derivations are logged for review
only in `unpointed_letters_anomalies.json`, never applied. `migration_report.json`
holds the full verification record: 264,217 words, `v_words` 0 differing rows,
0 FK violations, 0 lexicon round-trip mismatches. `migrate_v2.py` also asserts
that re-joining each composite Strong's `strongs_components` rows in `seq`
order reproduces the raw `strongs` string exactly (1,865/1,865 pass).

Attribution: the WLC Hebrew text is public domain; the OSHB
lemma/morphology annotations (used for Strong's fill and morphology parsing,
pinned at `3d15126fb1ef74867fc1434be1942e837932691f`) are CC BY 4.0.

Diagrams: `er_diagram_v2.png/.svg` (from `er_v2.py`), `dfd_v2.png/.svg` (from
`dfd_v2.py`, level-0 DFD incl. deployment), `context_v2.png/.svg` (from
`context_v2.py`, level-0 context). The v1 diagrams are kept for the record.
Semantic review 2026-09-28 verified every relationship against `schema_v2.sql`
and corrected two ER errors (inverted WORDS→STRONGS_SOURCES markers;
LEXICON_YLT_CONTEXT wrongly targeting YLT_VERSES) — see NOTATION_LEDGER §11.

Staging: `website/app_v2.py` (env-configured: `APP_DB`, `BIBLE_DB`, `USER_DIR`,
`PORT`, `SCRIPT_NAME`) serves `bible_v2.db` byte-identically to v1 on 13
representative routes. On the laptop (`/opt/bible`): `bible_v2.db` is
bit-identical to the local build (SHA-256 `4cacd562…e579e282`); supervisord
program `bible-v2` serves it on 127.0.0.1:5058 behind Apache `/bible-v2`
(inserted before `/bible`), with a separate app DB and choice directory and
`SCRIPT_NAME=/bible-v2`, while live `/bible` → 127.0.0.1:5057 (`app.py` +
v1 `bible.db`) stays untouched. Verified 2026-09-28: 13/13 routes 200 on the
internal port, 7/7 through the in-distro Apache proxy, live `/bible`
regression 200s, and the full write path (translation create, choice POST,
264,217-byte choice file, reading view, 69,647-line export — test data
removed afterward). The distro rebooted ~1 h after setup and both programs
self-recovered; post-reboot health re-verified. Direct external access from
this VM to the laptop was not reachable (curl 000/52), so no external claim
is made — the complete Apache proxy path was verified from inside the WSL
distro. **Live cutover DONE 2026-09-28 ~17:15 PDT** (Kit: "go live with it both
on github and on the laptop"): supervisord `bible` runs `app_v2.py` on
127.0.0.1:5057 with `BIBLE_DB=/opt/bible/bible_v2.db`; `/bible` + direct 5057
return 200; word/book/verse pages 200; the normalized corpus is now the
production corpus.

YLT word alignment (U-1, re-measured 2026-09-24): anchored-bridge method scores
precision 0.7941 / recall 0.4506 on a 30-verse hand-aligned gold set
(`eval/ylt_gold.tsv`, 770 pairs); corpus coverage 325,284/575,877 YLT tokens
mapped (56.4850%), 171,065/252,495 Hebrew words hit (67.7499%), per-book
41.25%–77.81%; `lexicon.ylt_renderings_computed` populated on 95,967/126,869
rows (75.6426%). Computed best-effort, NOT authoritative.

## Website (built 2026-09-22, Flask + SQLite)

- Over each Hebrew word: a drop-down box for choosing that word's rendering.
- Drop-down options: the **KJV** rendering, the **Young's** rendering
  (COMPUTED via KJV-bridge word alignment — labeled "Young's (computed)" in the
  UI; see U-1 for honest coverage numbers), and **other** — user-defined, for
  the academic pass.
- Choosing word by word builds and saves the user's own translation (named
  translations; per-word choices persist as **one byte per word** in
  `website/user_data/translation_<id>.choices` — 264,217 bytes, byte at offset
  `word_id − 1` = the selected drop-down item number, 0 = default).
  Multi-value "Other" renderings live in `website/app.db` (`other_option` table).
- Browse: `/` books → `/book/<n>` chapters → `/chapter/<n>/<c>` verses →
  `/verse/<n>/<c>/<v>` words. Reading view `/reading/<tid>/<n>/<c>/<v>`;
  export `/export/<tid>`; word detail `/word/<wid>` (pointed/unpointed, letters,
  affixes (normalized U-7 `*_disp` display columns), root code, Strong's,
  renderings, contexts, verses).
- `bible.db` is opened read-only; all user data lives in `website/app.db`
  (`app_user`, `translation`, `other_option` tables — `website/schema.sql`) plus
  the per-translation byte files in `website/user_data/` (one byte per word;
  git-ignored, personal data stays local).
  Run: `cd website && ./venv/bin/python app.py`
  (port 5057).

## Diagrams

Text-first: `website/website_er.mmd` and `website/website_system.mmd` are the
diagram sources (Mermaid — renders live on GitHub below). The `.png`/`.svg`
copies are built from `website/website_diagrams.py` (matplotlib).

<!-- MERMAID-ER-START -->
```mermaid
%% Website database — entity-relationship diagram (app.db + choice files).
%% Text source of website/website_er.png/.svg. Rendered live on GitHub
%% from the ```mermaid fence in README.md.
%% The website's own storage. bible.db (corpus) stays read-only;
%% every word_id here points into bible.db words.
erDiagram
    APP_USER {
        int user_id PK
        string name
        string created_at
    }
    TRANSLATION {
        int translation_id PK
        int user_id FK
        string name
        string description
        string created_at
        string updated_at
    }
    OTHER_OPTION {
        int option_id PK
        int translation_id FK
        int idx "1-based creation order within the translation"
        string text
        string created_at
    }
    CHOICES_FILE {
        string path PK "translation_{id}.choices"
        int size_bytes "264217, one byte per Hebrew word"
        int byte_offset "word_id minus 1"
    }
    APP_USER ||--o{ TRANSLATION : "one user, many translations"
    TRANSLATION ||--o{ OTHER_OPTION : "multi-value Other options"
    TRANSLATION ||--|| CHOICES_FILE : "one choice file per translation"
```
<!-- MERMAID-ER-END -->

<!-- MERMAID-SYSTEM-START -->
```mermaid
%% Website — system diagram. Text source of website/website_system.png/.svg.
%% Rendered live on GitHub from the ```mermaid fence in README.md.
%% Three stores: bible.db is the read-only corpus;
%% app.db + choice files hold the user's work.
flowchart TB
    B["Browser (Kit)<br/>verse reader: Hebrew word by word<br/>drop-down per word: KJV · Young's · Other<br/>my translations · reading view · export"]
    F["Flask app — website/app.py<br/>GET /book /chapter /verse /word<br/>POST /choice — saves the drop-down item-number byte"]
    DB[("bible.db — read-only corpus<br/>books · words · kjv_words · ylt_verses<br/>kjv_renderings · ylt_renderings (computed)<br/>lexicon · root_entry / root_form / root_vowel")]
    ADB[("app.db — the user's work<br/>app_user · translation · other_option<br/>created on first run")]
    CF[["user_data/translation_{id}.choices<br/>264,217 bytes — one byte per Hebrew word<br/>byte offset = word_id − 1<br/>0 = default · byte N = drop-down item N"]]
    B -->|"HTTP"| F
    F -->|"reads"| DB
    F -->|"reads + writes"| ADB
    F -->|"reads + writes bytes"| CF
    DB --> DD["Drop-down data, per Hebrew word<br/>KJV renderings (word-aligned)<br/>Young's renderings (computed verse-by-verse alignment)<br/>Other: user-typed (academic pass)"]
    ADB --> OO["Other options (multi-value)<br/>one row per custom rendering, per translation<br/>each becomes a drop-down item"]
    CF --> BR["Byte → text resolution<br/>0 → Hebrew shown (no choice)<br/>KJV / Young's items → rendering<br/>Other items → option text"]
```
<!-- MERMAID-SYSTEM-END -->
