Young's Literal Translation (YLT) — verse TSV ingest
====================================================
Directory: /home/hatch/workspace/bible-project/worker-out/ylt/
Date ingested: 2026-09-20
Ingest script: parse_ylt.py (kept in this directory for provenance/re-runs)
Raw package: engylt_usfm.zip (1.38 MB), extracted under usfm/

SOURCE
------
Download URL: https://ebible.org/Scriptures/engylt_usfm.zip
(The task's suggested URL pattern "eng-ylt_usfm.zip" returned HTTP 404; the
actual current ebible.org identifier is "engylt", found via web search and
verified by successful download. The task's https://ebible.org/eng-ylt/ page
could not be fetched by the browser tool this session; the license page below
was retrieved directly.)

LICENSE
-------
Public domain. Stated on the ebible.org license page for this translation,
https://ebible.org/engylt/copyright.htm :

  "Young's Literal Translation"
  "Young's Literal Translation of the Holy Bible"
  "Public Domain"
  "Language: ENGLISH (English) / Dialect: archaic British / Translation by: Robert Young"
  "This public domain Bible translation is brought to you courtesy of eBible.org."

The same statement ships inside the zip itself (usfm/copr.htm). No copyrighted
material was used; YLT (Robert Young, 1862/1898 revision) is public domain.

OUTPUT
------
File: ylt_verses.tsv
Header: book_num<TAB>chapter<TAB>verse<TAB>text
Rows: 23,145 verses (Old Testament only, books 1-39 in the project's
Protestant numbering; the zip also contains the 27 NT books, which were not
parsed per the project's OT scope).

text = verse text with USFM markers stripped and whitespace normalized.
The engylt USFM proved unusually clean: a marker survey of all 39 OT files
found only \id, \h, \toc1-3, \mt1, \c, \p, \v — no footnotes, cross-references,
or character/word markers at all. The parser strips any stray markers
defensively and reported zero anomalies (no duplicate references, no empty
verse texts, no unrecognized lines).

Validation performed:
- 23,145 verse rows = the standard Protestant OT verse count.
- Chapter structure verified against canonical Protestant chapter counts for
  all 39 books (e.g. Genesis 50, Psalms 150, Isaiah 66, Malachi 4) — match.
- Every TSV row has exactly 4 tab-separated fields; zero backslash characters
  remain in the text column.
- Spot checks: Gen 1:1, Psa 23:1, Mal 4:6 all correct.

PER-BOOK VERSE COUNTS (book_num, USFM code, name, verses)
---------------------------------------------------------
 1  GEN  Genesis             1533
 2  EXO  Exodus              1213
 3  LEV  Leviticus            859
 4  NUM  Numbers             1288
 5  DEU  Deuteronomy          959
 6  JOS  Joshua               658
 7  JDG  Judges               618
 8  RUT  Ruth                  85
 9  1SA  1 Samuel             810
10  2SA  2 Samuel             695
11  1KI  1 Kings              816
12  2KI  2 Kings              719
13  1CH  1 Chronicles         942
14  2CH  2 Chronicles         822
15  EZR  Ezra                 280
16  NEH  Nehemiah             406
17  EST  Esther               167
18  JOB  Job                 1070
19  PSA  Psalms              2461
20  PRO  Proverbs             915
21  ECC  Ecclesiastes         222
22  SNG  Song of Solomon      117
23  ISA  Isaiah              1292
24  JER  Jeremiah            1364
25  LAM  Lamentations         154
26  EZK  Ezekiel             1273
27  DAN  Daniel               357
28  HOS  Hosea                197
29  JOL  Joel                  73
30  AMO  Amos                 146
31  OBA  Obadiah               21
32  JON  Jonah                 48
33  MIC  Micah                105
34  NAM  Nahum                 47
35  HAB  Habakkuk              56
36  ZEP  Zephaniah             53
37  HAG  Haggai                38
38  ZEC  Zechariah            211
39  MAL  Malachi               55
TOTAL: 23,145 verses, 929 chapters.

ALIGNMENT ASSESSMENT (honest)
----------------------------
Achieved: VERSE-LEVEL alignment only.
NOT achieved: word-level alignment of YLT to Hebrew — and none was fabricated.

Reasons:
1. The engylt USFM contains no word-level annotation whatever. There are no
   \w markers with Strong's numbers, no morphology tags, no lemma attributes —
   the marker survey found only paragraph/chapter/verse markers. There is
   simply no Hebrew<->English word mapping in the data.
2. No public aligned YLT-to-Hebrew dataset exists to join against.
3. YLT is a deliberately literal translation, so per-verse correspondence
   with the Hebrew source is close — but "close correspondence" is not a word
   alignment, and inventing one (e.g. naive token-position pairing) would be
   fabrication, which the task explicitly forbids.
4. A genuine word alignment would require (a) an external Hebrew source text
   (e.g. the freely-licensed Westminster Leningrad Codex / Open Scriptures
   Hebrew Bible) plus (b) either manual annotation or statistical word
   alignment, whose output is probabilistic and would need its own validation.
   That is future work, not something derivable from this package.

What the TSV supports: verse-level joining of YLT against any other
verse-referenced dataset (Hebrew text, other translations, lexicons keyed by
reference). It does not support word-level joins.
