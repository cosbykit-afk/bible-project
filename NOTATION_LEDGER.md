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
| Strong's number | H-prefix index (H1–H8674) linking a Hebrew word to lexicon entries. Column mostly empty in Kit's files; filled via OSHB crosswalk. |
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
| `~/workspace/bible-project/bible.db` | SQLite database (build in progress) |
| `~/workspace/bible-project/BUILD_NOTES.md` | Build sources, licenses, coverage stats (pending) |
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

## 7. Unresolved items

- **U-1** (2026-09-20): YLT word-level alignment — verse-level is certain; word-level is best-effort. Awaiting DB build report for the achieved level.
- **U-2** (2026-09-20): Prophets.ods Psalms sheet (62 cols, stray `]צ`, trailing numbers) and Hosea sheet (1024 cols, stray values) contain junk columns. To be cleaned in the pipeline; cleaning log goes in BUILD_NOTES.md.
- **U-3** (2026-09-20): Canonical word source undecided — BibleFull's Bible sheet vs Prophets.ods per-book sheets. Awaiting diff in the DB build report.
- **U-4** (2026-09-20): `Var` and `Notes` columns in the notes sheet have no documented meaning yet. Kit to define, or drop.
- **U-5** (2026-09-20): "Green literal translation" read as Young's Literal Translation; Kit confirmed the plan containing YLT on 2026-09-20. Closed unless corrected.
- **U-6** (2026-09-20): Website stack and hosting undecided. Flask + SQLite is the working assumption; Kit hasn't chosen.
