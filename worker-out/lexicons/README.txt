Hebrew lexicon glosses for the Bible database project
=====================================================
Files
-----
glosses.tsv   UTF-8 TSV, header: strongs<TAB>source<TAB>gloss
              One row per (strongs, source); source is "bdb" or "strongs_he".
              Total rows: 17347  (bdb: 8673, strongs_he: 8674)

Attribution (per source license, see below):
  Lexicon content: Open Scriptures Hebrew Bible Project,
  https://github.com/openscriptures/HebrewLexicon

Source 1 — "bdb" (Brown-Driver-Briggs glosses, keyed by Strong's number)
-----------------------------------------------------------------------
Repository: https://github.com/openscriptures/HebrewLexicon
Commit:     21c9add13bc727d3a951361778e97e3ff7afd1ce (master, shallow clone 2026-09-20)
Files used: BrownDriverBriggs.xml (11,845 BDB entries) +
            LexicalIndex.xml (xref strong -> bdb id mapping)

License (exact statement from the repo's readme.md, lines 53-56;
also stated the same way on the repo home page):
  "These files are released under the Creative Commons Attribution 4.0
   International license. The actual text of Brown, Driver, Briggs and
   Strong's Hebrew dictionary remain in the public domain. For attribution
   purposes, credit the Open Scriptures Hebrew Bible Project."

License note: the XML files are CC-BY 4.0, but the repo itself states the
underlying BDB (1907) and Strong's (1890) dictionary texts remain in the
public domain. The glosses in glosses.tsv are the underlying dictionary
definitions (public-domain text), not the XML markup/editorial structure.
No HALOT or any copyrighted lexicon was used. Attribution to the Open
Scriptures Hebrew Bible Project is given above, satisfying the CC-BY term.

Entries ingested: 8673 Strong's numbers.
Coverage: H1-H8674 with one gap: H2007 is not present in LexicalIndex.xml
  (no xref maps to it), so there is no BDB row for H2007.
Gloss construction: all <def> texts of the mapped BDB entry, joined by
  "; " (multiple senses joined in document order, defs within a sense
  joined by ", "; top-level defs precede senses). Entries without <def>
  (4,516 of 11,845 are cross-references such as "v. II. אבה") fall back to
  the entry's plain text (scripture refs and status markup stripped).
  532 Strong's numbers map to more than one BDB entry (e.g. H122 -> 2
  entries); their glosses are merged with "; " in index document order.
No BDB xref target was missing from BrownDriverBriggs.xml and no mapped
entry yielded an empty gloss: zero BDB rows dropped.

Source 2 — "strongs_he" (Strong's Hebrew Dictionary glosses)
------------------------------------------------------------
Repository: https://github.com/openscriptures/HebrewLexicon
Commit:     21c9add13bc727d3a951361778e97e3ff7afd1ce (master, shallow clone 2026-09-20)
Files used: HebrewStrong.xml (entries natively keyed id="H<n>")

License: same statement as above (readme.md lines 53-56) — the actual
text of Strong's Hebrew dictionary (original 1890) remains in the public
domain; the XML wrapper is CC-BY 4.0; attribution given above. No
copyrighted Strong's derivative was used.

Entries ingested: 8674 Strong's numbers.
Coverage: complete H1-H8674, no gaps.
Gloss construction: plain text of the entry's <meaning> element
  (contains the <def> definition words). H3390 ("Jerusalem") has no
  <meaning> or <usage> in the source; its <source> text
  "(Aramaic) corresponding to 3389" was used instead. All other entries
  supplied a non-empty gloss. Zero rows dropped.

Entries dropped (all sources)
-----------------------------
None beyond the gaps listed above. H2007 has no BDB row (not indexed in
the source LexicalIndex.xml); H3390's Strong's row uses the fallback
described above.

Data-quality note on the source XML
-----------------------------------
8 LexicalIndex xref rows carry truncated, non-numeric "strong" attributes
(strong="b","c","d","i","k","l","m","s") — apparent data errors; they could
not be mapped to any Strong's number and were skipped (they add no
coverage; the numeric strongs for those words are present elsewhere).
