KJV WORDS DATASET — README
============================
Project: Hebrew Bible database (books 1-39, Protestant OT order)
Built: 2026-09-20 by a background worker
Output: kjv_words.tsv  (header: book_num<TAB>chapter<TAB>verse<TAB>kjv_pos<TAB>kjv_word<TAB>strongs)

1. SOURCE CHOSEN
---------------
Primary source: CrossWire SWORD "KJV" module, Version 3.1
  Download URL: https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/KJV.zip
  (local copy kept as KJV-crosswire-3.1.zip; module config kept as kjv.conf.source)
  Module description: "King James Version (1769) with Strongs Numbers and Morphology"
  Format: SWORD zText (compressed), OSIS markup, UTF-8. OT Strong's keying by
  The Bible Foundation (http://www.bf.org).

Cross-check source (independent, NOT the primary parse): ebible.org eng-kjv USFM
  URL: https://ebible.org/Scriptures/eng-kjv_usfm.zip
  (also public domain; used only to verify verse/chapter counts and spot-check
  word text — its word-level Strong's keying differs in granularity, see §5)

No fallback was needed: the SWORD KJV module is freely licensed (see §2), so the
verse-level fallback was not used and there is no Strong's-tagging gap.

2. LICENSE EVIDENCE (quoted verbatim from the source itself)
------------------------------------------------------------
File: mods.d/kjv.conf inside KJV.zip (saved here as kjv.conf.source),
also served live at http://www2.crosswire.org/ftpmirror/pub/sword/raw/mods.d/kjv.conf
and on the CrossWire module info page
(https://crosswire.org/sword/modules/ModInfo.jsp?modName=KJV).

  "Any copyright that might be obtained for this effort is held by CrossWire
   Bible Society © 2003-2023 and CrossWire Bible Society hereby grants a
   general public license to use this text for any purpose."

  DistributionLicense=GPL
  TextSource=https://gitlab.com/crosswire-bible-society/kjv

The base KJV text is public domain (rights held by the Crown of England; the
conf's About field notes this). No copyrighted Bible text (NIV/ESV/NASB/etc.)
was fetched or stored at any point.

3. TOTALS
---------
  Verses parsed:            23,145  (every OT verse, Gen 1:1 .. Mal 4:6;
                                     verse sequence verified identical to the
                                     eng-kjv USFM versification)
  Total KJV word rows:     610,324
  Words carrying a Strong's number: 569,583  = 93.32% of KJV words
  Words without a Strong's number:   40,741  =  6.68%
     of which marked as added/italicized in the source: 22,881
     (<transChange type="added"> — the translators' supplied words)
  Distinct Strong's numbers are ALL Hebrew ('H' prefix; OT only). Number formats
  as found in the source, zero-padded variably: H07225, H0430, H0853, H01, etc.
  (kept exactly as found, uppercased; no re-padding).
  Words with 2 Strong's numbers: 4,938 | with 3: 85  (comma-separated in `strongs`)
  Keyed phrases in source: 227,195  (see §5 on phrase-level keying)

4. PARSING DECISIONS / ANOMALIES
--------------------------------
a) Phrase-level Strong's keying. The module keys English PHRASES, not single
   words: e.g. <w lemma="strong:H07225">In the beginning</w> — all three English
   words carry H07225 in this table; <w lemma="strong:H0853 strong:H01254">created</w>
   gives "created" the value "H0853,H01254". This is why 93.3% of words carry a
   number (function words inside keyed phrases inherit the phrase's number),
   vs ~37% in the word-level ebible USFM keying. Where both sources key the same
   content word, the numbers agree (spot-checked Gen 1:1-3, Exod 20:3, Job 1:1,
   Isa 53:5, Mal 4:6 — word text identical in all samples).
b) Psalm titles INCLUDED. 116 canonical psalm titles (type="psalm") and 22 Psalm
   119 acrostic titles are kept as part of verse 1 with their Strong's numbers
   (e.g. Ps 23:1 begins "A Psalm of David[H04210]..."). They are canonical="true"
   in the source and align with Hebrew verse 1 (titles) in the OSHB text.
   Consequence: KJV verse 1 of such psalms contains both title and body text.
c) divineName uppercased. <divineName>Lord</divineName> is stored "LORD" (as
   printed in KJV). 6,552 occurrences.
d) Dropped: study footnotes (<note type="study">, 6,673 — they duplicate verse
   words in <catchWord>), book/chapter headings (<title type="main"/"chapter">),
   paragraph milestones, chapter/book boundary markers.
e) Kept as words: engraved inscription text (Exod 28:36; 39:30 "HOLINESS TO THE
   LORD"), Psalm 119 acrostic markers — including the 22 standalone Hebrew
   letters (e.g. "א") which appear as kjv_word values with empty strongs.
f) Punctuation stripped from word edges only; internal apostrophes/hyphens kept
   ("LORD's", "well-beloved"). Source typography kept verbatim otherwise:
   2,286 rows contain non-ASCII (curly apostrophes e.g. "wife’s", en-dashes e.g.
   "Tubal–cain", "Beth–el") exactly as in the module.
g) Verse-numbering: standard KJV/Protestant versification throughout (verified:
   23,145 verses incl. Ps 119 = 176 vv, Joel 2 = 32 vv, Mal 4 = 6 vv). The
   module's zText index contains 969 structural records (book/chapter boundary
   markers, importer milestone) which were correctly skipped — final verse
   sequence matches the USFM versification exactly, no duplicates, no gaps.
h) The module also contains the NT (Greek 'G' Strong's); it was NOT ingested —
   project canon is books 1-39 (OT) only.

5. VERIFICATION PERFORMED
-------------------------
- zText decode per the jsword ZVerseBackend spec (10-byte verse recs, 12-byte
  block recs, zlib blocks): all 40 blocks decompressed with exact size match.
- 23,145 verses emitted; (book,chapter,verse) sequence byte-identical to the
  independent eng-kjv USFM versification (929 chapters, per-chapter counts equal).
- TSV integrity: 610,324 data rows, 6 tab-separated columns on every row,
  kjv_pos strictly 1..N within each verse (0 breaks), no tabs/newlines in fields.
- Content spot-checks vs USFM parse: word text identical on all sampled verses;
  Strong's numbers agree where both key the same word (granularity differs per §4a).

6. FILES IN THIS DIRECTORY
---------------------------
  kjv_words.tsv          the dataset (13.6 MB)
  build_kjv_words.py     the parser (zText decode + OSIS handling)
  decode_ztext.py        exploratory zText decoder (superseded by build script)
  parse_stats.json       parse counters
  kjv.conf.source        module config incl. license statement (provenance)
  KJV-crosswire-3.1.zip  original module download (provenance)
  README.txt             this file
