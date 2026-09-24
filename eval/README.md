# YLT↔Hebrew alignment gold set (`ylt_gold.tsv`)

Hand-aligned evaluation set for U-1 (2026-09-24). 30 verses, 335 Hebrew
words, 770 expected `(word_id, ylt_word_pos)` pairs:

- Genesis 1:1–12 — narrative
- Psalms 23:1–6 — poetry
- Isaiah 53:1–12 — prophecy

Columns: `book, chapter, verse, word_id, word_pos, hebrew, strongs, ylt_pos, note`.
`ylt_pos` is a comma-separated list of 1-based YLT token positions, or empty
when the Hebrew word has no YLT token (4 such words in the set).

## Alignment policy (applied by hand, 2026-09-24)

1. A Hebrew word maps to the YLT token(s) that translate it.
2. English function words rendering Hebrew prefixes attach to that Hebrew
   word (e.g. the "in" of בראשׁית → בראשׁית).
3. H853 (את accusative marker) maps to nothing when untranslated.
4. Bracketed YLT editorial insertions (e.g. "[is]") are unmapped.
5. Construct-state "of" attaches to the genitive (following) word.
6. Unbracketed copulas ("is/are") attach to the predicate Hebrew word.
7. Restructured clauses map by sense, not by surface order.
8. Words YLT drops get an empty expected map, so any predicted token
   counts as a precision error.

## Scoring

`python3 build_ylt_align.py --eval` scores predicted
`(word_id, ylt_word_pos)` pairs against this set: precision = TP/predicted,
recall = TP/770. Predictions on the 4 empty-map words are false positives.
The H3068 (divine-name) words in the set are additionally checked for
drift: any predicted YLT token outside the gold map is a drift error.

Status note: this gold set measures the COMPUTED alignment only. The
alignment remains best-effort and NOT authoritative (NOTATION_LEDGER U-1).

## Measured results (2026-09-24, `build_ylt_align.py --eval`)

| method | precision | recall | predicted pairs | true positives |
|---|---|---|---|---|
| baseline | 0.6911 | 0.4766 | 531 | 367 |
| **anchored** (winner) | **0.7941** | 0.4506 | 437 | 347 |
| propagated | 0.7941 | 0.4506 | 437 | 347 |

The propagated variant produced zero propagated predictions on this set
(and zero propagated rows on the full 23,006-verse corpus), so the shipped
table is the anchored bridge. H3068 divine-name check: 0 drift pairs under
the anchored bridge (baseline: 1 wrong YLT token attached to an H3068 word);
H3068 misses remain — recall gaps, not mis-maps.
