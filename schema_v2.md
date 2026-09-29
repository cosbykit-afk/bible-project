# Bible database — normalization design (v2)

**Status:** approved by Kit 2026-09-28 ("the schema looks great").
**Live cutover DONE 2026-09-28 ~17:15 PDT** on Kit's "go live with it both on
github and on the laptop": supervisor `bible` runs `app_v2.py` on port 5057
against the normalized `bible_v2.db`; Apache `/bible`→5057 unchanged.
Pre-change backups + ROLLBACK.txt in
`/opt/bible/backups/pre-cutover-2026-09-28/`.
**Source DB:** `bible.db` v1 (198,459,392 bytes, 2026-09-27 build; 264,217 words).
**Migration:** `migrate_v2.py` builds `bible_v2.db` from `bible.db`.
**Proving ground:** the laptop deploy (`/opt/bible`, supervisord `bible`,
Apache `/bible` → 127.0.0.1:5057) — staging instance `bible-v2` on port 5058
against `bible_v2.db`, verified 2026-09-28 (13/13 internal routes 200, 7/7
in-distro Apache-proxy routes 200, live `/bible` regression 200s, full write
path + cleanup; both programs self-recovered after a later distro reboot).
**Migration assertion:** `migrate_v2.py` asserts every composite Strong's
value re-joins from its ordered `strongs_components` rows to the exact raw
string (1,865/1,865 pass).

## 1. What is wrong with v1 (evidence)

| # | Sin | Evidence |
|---|---|---|
| 1 | No foreign keys anywhere | `PRAGMA foreign_key_list(words)` returns zero rows; `integrity_check` is `ok` only because nothing is enforced |
| 2 | `(book, chapter, verse)` repeated on every row | `words` (264,217 rows), `kjv_words` (610,324 rows), `ylt_verses` (23,145 rows) each carry the triple with no `verses` table |
| 3 | Affix columns duplicated | `words` carries `prefix1..3, base_word, suffix1..2` **and** `_disp` variants, all functionally dependent on `(root_id, root_form_seq)` already in `root_form` (verified: 0 FD violations) |
| 4 | Derived columns stored as if source | `word_unpointed`, `letters` (strip vowels from `word_pointed`); `root_code` = `root_id.root_form_seq.root_vowel_seq` formatted — v2 preserves the stored values verbatim rather than adjudicating them (§4) |
| 5 | Lookup values inlined | `strongs` TEXT on 258,209 rows (8,674 distinct); `morph` TEXT on 264,138 rows (3,437 distinct); `strongs_source` 4-value vocabulary as free TEXT |
| 6 | 1NF violations: multi-value blobs | `lexicon.kjv_renderings`, `.ylt_renderings_computed` (`' | '`-separated), `.ylt_contexts` (`' ‖ '`-separated), `.found_verses` (`'; '`-separated) |
| 7 | Missing keys | `kjv_renderings` (631,950 rows) and `ylt_renderings` (337,601 rows) have no PK; `glosses` no declared PK |
| 8 | Orphan verses invisible | 139 English-versification verses (e.g. Gen 31:55 = Heb 32:1) exist in `ylt_verses`/`kjv_words` but not in `words`; a strict FK to a words-derived verse list would fail |

## 2. Target schema (v2)

Conventions: `INTEGER PRIMARY KEY` surrogate keys only where the natural key
is composite or unstable; natural TEXT keys (`strongs`) keep their stable form.
Every FK is declared and enforced (`PRAGMA foreign_keys=ON` at migration and
in the app). Columns that are pure derivations of other columns live in views,
not tables — except `unpointed`/`letters`, which are preserved legacy values
kept verbatim from v1 (see §4).

```
books(book_id PK, name_en, name_he)
  -- book_id 1..39 preserved (was book_num)

verses(verse_id PK, book_id FK→books, chapter, verse, UNIQUE(book_id, chapter, verse))
  -- UNION of (book, chapter, verse) from words, ylt_verses, kjv_words.
  -- Covers the 139 English-versification orphans (§1.8) so every FK resolves.

strongs(strongs TEXT PK, language TEXT NOT NULL)
  -- 'H7225' etc.; language from leading letter (all H in this corpus)

strongs_sources(source_id PK, source TEXT UNIQUE)
  -- 1:'oshb', 2:'oshb-split', 3:'kit'. words.strongs_source_id NULL ⟺ strongs NULL.

morph_patterns(pattern_id PK, pattern TEXT UNIQUE NOT NULL,
               language TEXT, parse_status TEXT, parse_notes TEXT)
  -- 3,437 distinct OSHB morph strings, verbatim. NULL FK on words = the 79
  -- words with no morph (documented, not silently dropped).

morph_segments(segment_id PK, pattern_id FK→morph_patterns, seq,
               code TEXT, pos TEXT, pos_name TEXT,
               stem TEXT, stem_name TEXT, conj TEXT, conj_name TEXT,
               type TEXT, type_name TEXT,
               person TEXT, person_name TEXT,
               gender TEXT, gender_name TEXT,
               number TEXT, number_name TEXT,
               state TEXT, state_name TEXT,
               UNIQUE(pattern_id, seq))
  -- One row per '/'-separated segment. Code meanings from the authoritative
  -- OSHB Hebrew Morphology Codes doc (openscriptures.github.io/morphhb/
  -- parsing/HebrewMorphologyCodes.html, fetched 2026-09-28; CC-BY-4.0,
  -- attribution recorded in NOTATION_LEDGER §6). COMPUTED parse: every
  -- segment letter must be in the documented sets or the pattern is flagged
  -- parse_status='unparsed' and logged. Greedy slot assignment follows the
  -- doc's feature order (gender, number, state); ambiguous codes (e.g.
  -- Aramaic 'd' = dual vs determined) resolve to the earliest slot.
  -- Doc note 5 ('x' = placeholder for unknown values when a necessary value
  -- follows) resolves the Aramaic Nxxxa patterns: type/gender/number unknown,
  -- state absolute (recorded as unknown, never asserted). One pattern stays
  -- unparsed: 'AT' (5× Aramaic דִּי, Daniel) — bare particle with no type;
  -- the doc defines no bare-particle code and note 5 does not apply
  -- (nothing follows). Kept verbatim with parse_status='unparsed'.
  -- Parse ≠ linguistic verdict.

words(word_id PK, orig_word_id TEXT, verse_id FK→verses NOT NULL,
      word_pos, pointed TEXT NOT NULL,
      unpointed TEXT, letters TEXT,            -- PRESERVED VERBATIM from v1, §4
      strongs FK→strongs,                       -- NULL: 6,008 words
      strongs_source_id FK→strongs_sources,     -- NULL ⟺ strongs NULL (CHECK)
      morph_pattern_id FK→morph_patterns,       -- NULL: 79 words
      is_aramaic NOT NULL DEFAULT 0,
      root_id FK→root_entry NOT NULL, root_form_seq NOT NULL, root_vowel_seq NOT NULL,
      FK(root_id, root_form_seq)→root_form, FK(root_id, root_form_seq, root_vowel_seq)→root_vowel,
      UNIQUE(verse_id, word_pos))

root_entry(root_id PK, root TEXT UNIQUE NOT NULL, word_count)
root_form(root_id FK, form_seq, prefix1, prefix2, prefix3, suffix1, suffix2,
          prefix1_disp, prefix2_disp, prefix3_disp, suffix1_disp, suffix2_disp,
          word_count, example_pointed, example_unpointed, PK(root_id, form_seq))
  -- _disp columns MOVED here from words (FD-verified, §1.3)
root_vowel(root_id, root_form_seq, vowel_seq, vowel_pattern, word_count,
           PK(root_id, root_form_seq, vowel_seq), FK→root_form)

lexicon(root_id, root_form_seq, vowel_seq, PK, FK→root_vowel)
  -- header only; the four blobs become child tables:
lexicon_kjv_rendering(root_id, root_form_seq, vowel_seq, seq, rendering, PK(..., seq))
lexicon_ylt_rendering(root_id, root_form_seq, vowel_seq, seq, rendering, PK(..., seq))
  -- seq preserves the build's frequency order
lexicon_ylt_context(root_id, root_form_seq, vowel_seq, seq, verse_id FK→verses,
                    context_text, PK(..., seq))
  -- 'Book c:v — text —' split into verse FK + YLT text
lexicon_found_verse(root_id, root_form_seq, vowel_seq, verse_id FK→verses,
                   PK(..., verse_id))
  -- 'Book c:v; ...' one row per verse

glosses(strongs FK→strongs, source, gloss, PK(strongs, source))

kjv_words(kjv_word_id PK, verse_id FK→verses NOT NULL, kjv_pos,
          kjv_word NOT NULL, strongs FK→strongs, UNIQUE(verse_id, kjv_pos))
  -- strongs NULL: 40,741 rows

kjv_renderings(rendering_id PK, word_id FK→words NOT NULL,
               kjv_word NOT NULL, kjv_strongs FK→strongs, method NOT NULL)

ylt_verses(verse_id PK FK→verses, text NOT NULL)

ylt_renderings(rendering_id PK, word_id FK→words NOT NULL,
               ylt_word NOT NULL, ylt_word_pos NOT NULL, label NOT NULL)
```

## 3. Views (compat + convenience; not storage)

- `v_words` — the old flat `words` row: `word_id, book, chapter, verse,
  word_pos, word_pointed (=pointed), word_unpointed (=unpointed),
  letters, prefix1..3, base_word (=root), suffix1..2, *_disp (from root_form),
  strongs, strongs_source, morph (=pattern), is_aramaic, root_id,
  root_form_seq, root_vowel_seq, root_code`. For ad-hoc queries and any
  third-party code written against v1.
- `v_lexicon` — old `lexicon` shape: header + the four blobs re-aggregated
  with `group_concat(... , ' | ')` in `seq` order (byte-identical to v1
  blobs where the split was lossless).
- `v_kjv_words`, `v_ylt_verses`, `v_glosses` — old shapes.
- `v_verse_coverage(verse_id, book, chapter, verse, n_words, has_kjv, has_ylt)`
  — makes the 139 orphans (§1.8) and 209 YLT-less verses visible instead of
  silently absent.

## 4. Derived-column policy

Dropped to views: `book/chapter/verse` on word rows, `root_code`,
`strongs_source` TEXT (→ FK). **Kept as stored columns:** `unpointed`,
`letters` — functionally dependent on `pointed` in v1's build, but the
migration **preserves v1's stored values verbatim** and does not re-derive
them. A normalization migration is a re-organization of data, not an
adjudication of legacy values: the 129 rows where a candidate strip rule
disagrees with the stored value (examples: split/merged tokens like word
71448 with empty `pointed` but stored `אכרת-לכ`, or word 84702 with stored
`ככ` against pointed `בְּנֵי`) may reflect source token splits, ingestion
mapping, or deliberate legacy choices — none of that is established. The
candidate rule and every disagreeing row are written to
`unpointed_letters_anomalies.json` for separate review; nothing there is
applied. `root_form.word_count`, `root_vowel.word_count`,
`root_entry.word_count` stay as build-maintained cached aggregates
(copied from v1).

## 5. What v2 does NOT change

- The website's `app.db` (users/translations/other_option) — already
  normalized; untouched. The byte-per-word choices files are Kit's standing
  directive, untouched.
- `word_id` values — stable across v1→v2, so existing translation choice
  files keep working.
- No data re-derivation: v2 is a re-organization of v1's data, not a new
  parse. (The morph *parse* in `morph_segments` is new computed data,
  clearly labeled per Kit's scoping rule.)

## 6. Verification (migration must prove)

1. Row counts: every v2 table/child-table reconciles to v1 (words 264,217;
   kjv_words 610,324; kjv_renderings 631,950; ylt_renderings 337,601;
   glosses 17,347; root_* and lexicon headers unchanged).
2. `PRAGMA foreign_key_check` → zero rows, on a FK-enforcing connection.
3. Blob round-trip: `v_lexicon` blobs equal v1 blobs for all 126,869 rows.
4. `v_words` row-for-row equals v1 `words` (modulo documented renames).
5. Website equivalence: staging app on v2 serves the same verse/word pages
   as live on v1 (diff of rendered HTML for a sample of verses).
