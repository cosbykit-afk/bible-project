# word_variants — method note

**Status:** built 2026-09-28 by `build_variants.py` (rerunnable, idempotent;
drops/rebuilds only `word_variants`). Three consecutive builds produce
byte-identical table content (SHA-256 `b0edc3e748f298b4` over all columns).

## Why this table exists

Kit's ruling on the spelling-convention ambiguity: the word ID stays single,
but spellings are multi-value. `word_variants` is a one-to-many relationship
from `words(word_id)` accommodating alternate spellings, academic spellings,
and outright word-choice variants. The table **records variance; it does not
adjudicate** — no spelling is marked canonical. Every row carries `source`
and `basis` provenance; consumers choose by convention/source, never by an
implicit preference in the table.

## The two conventions

| convention | letter forms | maqaf | origin |
|---|---|---|---|
| `v1-medial` | medial only (כמנפצ, never sofit) | hyphen-minus U+002D | v1 house convention (13,530 rows end כ vs 0 ך; 38,865 end מ vs 0 ם) |
| `academic-final` | final forms ךםןףץ at segment end | maqaf U+05BE | OSHB/WLC (the scholarly text) |

## Sources

| source | meaning |
|---|---|
| `v1-stored` | copied verbatim from v1's `words` table |
| `oshb-verbatim` | resolution from `anomaly_resolutions.json` (word-by-word OSHB audit); `v1conv` rows are the same resolution rendered in v1 convention |
| `transduced-from-v1` | deterministic sofit/maqaf mapping applied to a v1-stored value |
| `conjectural` | explicitly conjectural reading (word 104753 only) |

## The transduction rule (bulk path, 264,088 words)

For each non-anomaly word, row 2 is derived from the v1-stored value:

1. `transduce_unpointed`: map כ→ך, מ→ם, נ→ן, פ→ף, צ→ץ when at end of string
   or immediately before `-`/`־`; then replace `-` with `־` (U+05BE).
2. `transduce_letters`: strip `־` from the transduced unpointed (sofit forms
   preserved from segment-final positions, matching the audit's convention,
   e.g. `לך־לכה־נא` → `לךלכהנא`).

Deviations from the task spec, documented:
- Spec listed כמנפ→ךםןףץ; **צ→ץ added** — Hebrew orthography requires it
  (3,298 segment-final צ in the corpus, e.g. ארץ); omitting it would emit
  invalid academic spellings.
- Letters are derived from the transduced *unpointed*, not transduced
  independently: v1 `letters` has no hyphens, so segment boundaries (which
  govern sofit) are only recoverable via the unpointed form. The invariant
  `letters == unpointed minus maqaf` holds for all 264,088 bulk words and is
  preserved by construction in the new rows.

Verification of the rule against the audit: transducing the audit's 129
`resolved_*_v1conv` forms reproduces its `resolved_unpointed` in **129/129**
cases and its `resolved_letters` (via the strip rule) in **128/129**. The
single exception is word 71448, whose file `resolved_letters` (`אכרתלכ`)
is internally inconsistent with its own `resolved_unpointed` (`אכרת־לך`,
strip gives `אכרתלך`). The file's value is stored verbatim with a `FLAG`
in `basis`; the table does not silently correct the audit.

## Population

- **264,088 normal words:** seq 1 = v1-stored (`v1-medial`); seq 2 =
  transduced (`academic-final`).
- **129 anomaly words:** seq 1 = v1-stored (`v1-medial`, `v1-stored`,
  basis cites anomaly class + confidence); seq 2 = OSHB resolution in v1
  convention (`v1-medial`, `oshb-verbatim`); seq 3 = OSHB resolution verbatim
  (`academic-final`, `oshb-verbatim`, basis cites OSHB book/chapter/verse,
  token positions, match method).
- **Word 104753** (2 Sam 18:20, medium confidence): seq 4 extra row, the
  conjectured reading כי־על/כיעל, source `conjectural` — conjecture lives in
  the variants table, not in the resolution rows.
- **Word 71448** (phantom row): seq 4 extra row, same stored text, basis
  documents the tokenization artifact (v1 split of OSHB Josh 9:7 tokens
  12–14; value itself verified correct).
- 7 punctuation-only words (pointed `׀`, empty unpointed/letters) get 2 rows
  with empty strings — empty is not NULL; the schema's NOT NULL holds.

## Verification (all pass)

- 528,565 rows: 264,088×2 + 127×3 + 2×4 (104753, 71448)
- every `words` row has ≥2 variants; exactly the 129 anomaly words have >2
- `variant_seq` dense from 1 per word; 0 NULLs; 0 FK violations;
  0 words rows unrepresented
- 15-row hand spot-check (anomaly + maqaf-joined + plain + edge cases) reviewed

## What this table does NOT do

- It does not change `words.unpointed`/`words.letters` (still v1 verbatim).
- It does not pick a winner between conventions or readings.
- The audit file's `resolved_letters` values are stored verbatim even where
  they disagree with the strip rule: 128/129 agree with
  `resolved_unpointed` minus maqaf; the 1 genuine inconsistency (71448:
  file has `אכרתלכ`, strip of `אכרת־לך` gives `אכרתלך`) is flagged in-row
  rather than silently corrected.

## Merge with textual variants (2026-09-30, Kit's decision)

`schema_var_notes.sql` (2026-09-29) defined a second, incompatible
`word_variants` for manuscript textual variants (variant_id PK; witness,
variant_type columns). Kit merged the two: ONE table, tagged by
`variant_kind` (`'spelling'` | `'textual'`, CHECK-enforced).

Column discipline by kind:

| column | `spelling` rows | `textual` rows |
|---|---|---|
| `unpointed` / `letters` | the spelling in a convention | unpointed form of the variant reading (for matching) |
| `variant_text` | NULL | the variant reading (Hebrew, may be pointed) |
| `convention` / `source` | NOT NULL (`v1-medial`/`academic-final`; `v1-stored`/`oshb-verbatim`/`transduced-from-v1`/`conjectural`) | NULL — provenance is `witness` |
| `witness` / `variant_type` | NULL | manuscript siglum (`LXX`, `DSS`, `SP`, …) / `orthographic`, `substantive`, … |
| `basis` | evidence note / rule citation | evidence note |

`variant_seq` continues per word across kinds: spelling rows occupy the low
seqs (1–2 bulk; 1–4 for the 129 anomaly words), textual rows append after.
`build_variants.py` emits the merged schema (`variant_kind='spelling'`) and is
the table's builder; `migrate_variants_merge.py` upgraded existing databases
in place (all 528,565 rows backfilled `'spelling'`, old-column values verified
byte-identical via EXCEPT both ways, 0 FK violations). No textual rows exist
yet — the apparatus is populated separately.

## Divergence

Local `bible_v2.db` now contains `word_alignment` (prior task) and
`word_variants`, plus indexes — it differs from the laptop staging copy
(`/opt/bible/bible_v2.db`, bit-identical as of the earlier SHA-256 check).
Re-shipping belongs with the other pending corrections; live cutover has since occurred (2026-09-28 ~17:15 PDT), so re-shipping now updates the live laptop copy.
