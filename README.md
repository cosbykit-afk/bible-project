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
| `kjv_renderings` | 409,930 | KJV word renderings aligned to Hebrew words |
| `kjv_words` | 610,324 | Raw KJV+Strong's word list |
| `ylt_verses` | 23,145 | Young's Literal Translation, verse level |
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

Coverage: 175,449 of 264,217 words carry a Strong's number (66.4%);
every one of those has at least one gloss. 134,625 words (50.9%) have a
KJV rendering. 4,405 Aramaic words flagged. The remaining gap is a
crosswalk alignment limitation (OSHB splits maqqef-joined words; Kit's
files don't) — see `oshb_crosswalk_report.json`.

## Sources (all public domain / freely licensed)

- Kit's spreadsheets: BibleFull (v 1).xlsx, Prophets.ods, Verses.ods
- OSHB / morphhb (Open Scriptures Hebrew Bible) — Hebrew text + Strong's + morphology
- KJV + Strong's (Crosswire)
- Young's Literal Translation (ebible.org eng-ylt, USFM)
- BDB + Strong's Hebrew dictionary (Open Scriptures HebrewLexicon)

## Status

Database built; website not yet started. Open items are tracked as `U-`
items in `NOTATION_LEDGER.md`.
