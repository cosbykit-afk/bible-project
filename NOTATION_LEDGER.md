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
  tuples group together), but a future cleanup pass could normalize these to
  Hebrew letters. Tracked as U-7.
- Strong's numbers are retained as a foreign key into the public-domain
  lexicons (KJV/gloss dropdowns), but the root code is the project's primary
  word numbering.

## 9. Unresolved items

- **U-1** (2026-09-20): YLT word-level alignment — verse-level is certain; word-level is best-effort. Update 2026-09-21: verse-level confirmed in DB (`ylt_verses`, 23,145 rows). Word-level remains best-effort; still open.
- **U-2** (2026-09-20): Prophets.ods Psalms sheet (62 cols, stray `]צ`, trailing numbers) and Hosea sheet (1024 cols, stray values) contain junk columns. Closed 2026-09-21: extra columns ignored as junk in the ingest (canon_report.json); Prophets sheets matched the canonical list at 99.85%.
- **U-3** (2026-09-20): Canonical word source undecided — BibleFull's Bible sheet vs Prophets.ods per-book sheets. Closed 2026-09-21: BibleFull's Bible sheet is canonical (264,217 rows); Prophets.ods used as a check.
- **U-4** (2026-09-20): `Var` and `Notes` columns in the notes sheet have no documented meaning yet. Kit to define, or drop.
- **U-5** (2026-09-20): "Green literal translation" read as Young's Literal Translation; Kit confirmed the plan containing YLT on 2026-09-20. Closed unless corrected.
- **U-6** (2026-09-20): Website stack and hosting undecided. Flask + SQLite is the working assumption; Kit hasn't chosen.
- **U-7** (2026-09-21): Affix columns are Kit's own uneven parsing — `prefix1`/`prefix2` often hold English glosses ("and, but") instead of Hebrew letters, and `prefix3` sometimes holds a whole preceding maqqef-joined word ("אל-ה"). The root numbering groups on these tuples exactly, so numbering is unaffected, but a future pass should normalize them to Hebrew letters for display.
