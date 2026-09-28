# Morphology corrections — method note (2026-09-28)

Builder: `apply_morph_corrections.py` (rerunnable, idempotent).
Research: `morphology_research.md` — findings only, no DB changes by the researcher.

## What was applied

**Established (9 tokens) — words re-pointed to corrected pattern rows:**

| words | change | basis |
|---|---|---|
| 5× דִּי (Dan 4:12, 4:20, 4:26, 5:5 ×2) | `AT` → `ATr` | The migration kept `AT` as `parse_status='unparsed'` on a misreading of the morphhb doc. The Particle types table defines `r` = relative; all 165 other דִּי tokens in the corpus are `ATr` (96 in genitive position); Gzella: דִּי connects genitive "A of B" and introduces relative/object clauses. All 5 are genitive "of". |
| מְנֵא ×2, תְּקֵל (Dan 5:25) | `ANxxxa` → `ANcmsa` | BDB Biblical Aramaic appendix: n.[m.] "mina", n.[m.] "shekel"; singular; absolute (no ־ָא determined ending). |
| וּפַרְסִין (Dan 5:25) | `AC/Nxxxa` → `AC/ANcmpa` | BDB n.[m.] "half-mina"; ־ִין = masculine plural absolute (Marshall); dual does not exist in Biblical Aramaic; type=c (common) is probable — the gentilic "Persians" wordplay is the known secondary reading, staged as a variant. |

`AC/ANcmpa` had no pattern row; the builder created it (pattern_id 3438) with
segments copied from the existing `AC/Ncmpa` composite structure. All other
target patterns (`ATr`, `ANcmsa`) already existed with parsed segments.

**Probable (3 tokens, Dan 5:26–28) — NOT re-pointed.** מְנֵא / תְּקֵל / פְּרֵס keep
`ANxxxa`; the probable `ANcmsa` reading is staged in `morph_variants` because
the participle re-reading ("numbered, weighed, divided") is a live alternative.

**Secondary readings — staged in `morph_variants` only, never assigned:**

- `AVQsmsa` on the 5:26–28 words: Daniel's verbal re-reading of the inscription
  (passive participle; implies re-vocalized תְּקִיל / פְּרִיס — only מְנֵא is
  formally identical in both readings).
- `AC/ANgmpa` on וּפַרְסִין: the gentilic "Persians" wordplay (cf. 5:28 וּפָרָס).

## morph_variants

One-to-many morphology apparatus, mirroring the `word_variants` philosophy:
variance is recorded, not adjudicated.

- `variant_seq 1` on every touched word = the legacy v1 code (`confidence='legacy'`,
  `source='v1-stored'`) — the original annotation is never lost.
- `seq 2` = the corrected (established) or probable code, with `pattern_id`
  pointing at the real pattern row where one exists.
- `seq 3` = secondary readings; `pattern_id` is NULL because these codes have
  no pattern row (they are not assigned to any word).
- Words with no row here: the v1 reading stands unchallenged.

## Deliberately untouched

- The 2 maqaf-merged דִּי tokens (דִּֽי־כְתַל, דִֽי־דַהֲבָא) absorbed the particle
  morphology into a following noun at v1 ingest — a pre-existing tokenization
  artifact, not a morphology question. Flagged for the tokenization-variance
  work, not fixed here.
- The 40 `Pdx__`-family `x` placeholders are legitimate (unnecessary person on
  demonstratives, doc note 5) — not problems.
- Honest gap from the research: Rosenthal's *Grammar of Biblical Aramaic* was
  not directly accessible (restricted copy); the דִּי classification rests on
  Gzella + Marshall + the doc + 165× corpus precedent. A Rosenthal section
  citation remains a worthwhile follow-up.
