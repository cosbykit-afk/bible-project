# word_alignment — method note

Date: 2026-09-28
Database: `~/workspace/bible-project/bible_v2.db` (local copy — see §12)
Builder: `~/workspace/bible-project/build_alignment.py` (rerunnable, idempotent)

## 1. What this table is

`word_alignment` is a **deterministic word-level alignment** joining, per
verse, one row-group per Hebrew word carrying that word's Hebrew word ID,
its primary KJV word ID, and its primary YLT rendering ID, plus satellite
rows so that **every** KJV word row and **every** YLT rendering row is
referenced exactly once. Rows within a verse are sequence-ordered in
diagram regions: subjects, verbs, objects, adjectives, adverbs, then
other/unresolved (Kit's "line upon line" ordering).

**This is deterministic morph+marker heuristics, NOT a full syntactic
parse.** No clause boundaries, construct chains, apposition, ellipsis,
fronting, subordination, or poetic parallelism are resolved. Every
`syntactic_role` is a provisional label with its exact basis recorded in
`role_basis`; §9 lists what the heuristics cannot do.

## 2. Schema (additive — no existing table was altered)

```sql
CREATE TABLE word_alignment(
  alignment_id   INTEGER PRIMARY KEY,
  verse_id       INTEGER NOT NULL REFERENCES verses(verse_id),
  seq            INTEGER NOT NULL,          -- dense 1..N per verse
  hebrew_word_id INTEGER REFERENCES words(word_id),
  kjv_word_id    INTEGER REFERENCES kjv_words(kjv_word_id),
  ylt_rendering_id INTEGER REFERENCES ylt_renderings(rendering_id),
  syntactic_role TEXT NOT NULL,             -- subject|verb|object|
                                           -- qualifier:adj|qualifier:adv|
                                           -- other|translator-supplied|
                                           -- unresolved
  role_basis     TEXT NOT NULL,             -- exact heuristic, see §7
  UNIQUE(verse_id, seq)
);
CREATE INDEX idx_alignment_hebrew ON word_alignment(hebrew_word_id);
CREATE INDEX idx_alignment_verse  ON word_alignment(verse_id, seq);
```

## 3. Input facts (established by completed database checks, 2026-09-28)

- Hebrew `words`: 264,217 · `kjv_words`: 610,324 · `kjv_renderings`: 631,950 ·
  `ylt_renderings`: 337,601 · verses: 23,354.
- KJV renderings cover 207,312 distinct Hebrew words; YLT renderings cover
  171,065. 56,905 Hebrew words have no KJV rendering; 93,152 have no YLT
  rendering. 79 Hebrew words have no morphology pattern.
- Morphology POS codes verified from `morph_segments`: `A` adjective,
  `C` conjunction, `D` adverb, `N` noun, `P` pronoun, `R` preposition,
  `S` suffix, `T` particle, `V` verb. Pronoun types: `d` demonstrative,
  `f` indefinite, `i` interrogative, `p` personal, `r` relative. Particle
  types: `a` affirmation, `d` definite article, `e` exhortation,
  `i` interrogative, `j` interjection, `m` demonstrative, `n` negative,
  `o` direct-object marker, `r` relative.
- **את marker identity (established):** 2,761 Hebrew words carry
  `strongs='H853'`; 100% of them have a `T/o` ("direct object marker")
  morphology segment, and no H853 token is Aramaic. The marker surfaces as
  a bare particle (`HTo`, also after `C` prefixes as `HC/To`), bound before
  a noun/pronoun in maqqef compounds (6,696 words with unpointed `את-…`,
  which OSHB does **not** split morphologically), and with pronominal
  suffixes (`HTo/Sp…`, e.g. אֹתוֹ "him").
- Academic grounding for the marker's function: אֵת is the definite
  direct-object marker — Gesenius–Kautzsch, *Hebrew Grammar*, §117.
- Translation cardinality (established): mappings are heavily 1:N, not
  1:1 — 171,991 Hebrew words have >1 distinct KJV rendering word; 103,815
  have >1 distinct YLT rendering word. YLT `word_id` is never NULL; all YLT
  rows are labeled `bridged`. 9,302 `(word_id, ylt_word)` groups are
  duplicated, though `(word_id, ylt_word_pos)` is unique. 4,921 KJV
  renderings point at a KJV token in a *different* verse than the Hebrew
  word (source-alignment imperfection, kept verbatim).

## 4. Alignment construction

Per verse, in Hebrew `word_pos` order:

1. **Base row** per Hebrew word (`hebrew_word_id` set). Its primary KJV
   link: the word's `kjv_renderings` texts in rendering-ID order, matched
   against `kjv_words` of the same verse; duplicate English text is claimed
   deterministically — the earliest unclaimed `kjv_pos` wins
   (`dup_text_hits` 258,772; `kjv_took_later_candidate` 48,591). Its
   primary YLT link: the rendering with the lowest `ylt_word_pos`.
2. **KJV satellite rows** for KJV tokens not claimed by any base row:
   - `translator-supplied` (`role_basis='no-rendering-reference'`, 81,594
     rows) if the token's text has no rendering reference anywhere in the
     verse — genuine translator additions (e.g. English copula "is"/"am",
     Gen 31:55's English-only versification, where *all* rows are
     satellites).
   - `other` (`role_basis='extra-kjv-rendering'`, 323,943 rows) if the text
     appears in rendering evidence but is an additional token.
3. **YLT satellite rows** (`role_basis='extra-ylt-rendering:<pos>'`,
   166,536 rows) for further YLT rendering rows — these represent 1:N
   rendering multiplicity, not translator-supplied source words (all YLT
   rows have a non-NULL Hebrew `word_id`).
4. 2,525 Hebrew words have renderings but no available KJV token in their
   verse (`kjv_null_despite_renderings`); their base rows carry KJV=NULL.

## 5. Diagram ordering (`seq`)

Dense 1..N per verse. Sort key per row: role region
(subject 0, verb 1, object 2, qualifier:adj 3, qualifier:adv 4, other 5,
translator-supplied 6, unresolved 7), then Hebrew `word_pos` (base rows),
then satellite kind and token position. The hand-check printout in the
build log shows each verse in this order (e.g. Gen 1:1: subject אלהים,
verb ברא, objects השמים/הארץ, בראשית as prepositional-phrase, את tokens,
then English satellites).

## 6. Lexical-head finding (established morph facts + one rule)

The head of a word is its **last** morph segment that is not `C`
(conjunction) or `S` (pronominal suffix), with two refinements found
necessary by hand-checking:

- A **trailing** `T/d` steps back to the lexical segment: in Aramaic the
  definite article is a *suffix* (emphatic state, e.g. מַלְכָּא `[N,Td]`),
  whereas in Hebrew it is a prefix (הַשָּׁמַיִם `[Td,N]`). Without this,
  Aramaic emphatic nouns were mislabeled `particle:definite article`.
- A standalone `R` is a preposition (בֵּין `[R]`), a standalone `T` a
  particle (אֲשֶׁר `[Tr]`, לֹא `[Tn]`); degenerate all-`C`/`S` patterns
  (כִּי `[C]`) fall back to the last segment so they label as conjunctions.

Prefixes before the head are inspected for `R` (prepositional phrase) and
`T/o` (object marker).

## 7. Role heuristics (exact rules; `role_basis` records which fired)

- `other` / `et-marker-token`: pure marker tokens — `strongs='H853'`
  (Hebrew) with a bare `T/o` head (1,037 rows).
- `object` / `et-marker-pronominal`: marker + pronominal suffix, the
  suffix *is* the object (e.g. אֹתוֹ; 1,724 rows).
- `object` / `et-marker`: (a) **self-marked** — `T/o` prefix, or bound
  `את-` in the surface text (unpointed `את-…`, since OSHB leaves these
  unsplit), on a noun/pronoun head; (b) **span-marked** — noun/pronoun
  head with no preposition prefix, inside the span opened by a pure marker
  and closed by the next verb, next marker, or verse end [GKC §117].
  Span + self-marked objects: 8,249 rows; total objects 9,973.
- `verb` / `morph-verb`: verbal head, **including participles and
  infinitives** (documented heuristic, not a finiteness claim) — 71,261.
- `subject` / `personal-pronoun`: independent personal pronoun, no
  preposition prefix (אָנֹכִי in Ex 20:2).
- `subject` / `unmarked-substantive`: other nouns with no preposition
  prefix — Hebrew subjects are unmarked nominatives, so this is the
  provisional default (104,349 incl. personal pronouns).
- `other` / `prepositional-phrase`: noun/pronoun with a preposition
  prefix (`בְּרֵאשִׁית`, לְדָוִד, מֵאֶרֶץ); `other` / `preposition` for bare
  `R` heads (בֵּין, עַל, וְלֶךְ־לְךָ).
- `qualifier:adj` / `morph-adjective` (13,893), `qualifier:adv` /
  `morph-adverb` (4,011); bound-`את־` adjectives (אֶת־יְחִידְךָ) stay
  qualifiers — they modify the object noun.
- `other` / `particle:<type>` (לֹא negative, אֲשֶׁר relative, אֵי
  interrogative…), `other` / `pronoun:<type>`, `other` / `conjunction`.
- `unresolved`: 85 rows — 78 with no morphology pattern, 6 with unparsed
  (`AT`) patterns, 1 Aramaic of the same kind.

**Aramaic rule:** Aramaic לְ־ is coded `T/o` but is ambiguous between
dative and accusative; without a parser it is conservatively treated as a
preposition prefix (→ `prepositional-phrase`), never as the Hebrew object
marker. Aramaic roles carry a `|aramaic` suffix on `role_basis`
(Dan 2:4 verified: מַלְכָּא/חֶלְמָא subjects, לְעָלְמִין "forever" PP).

## 8. Verification (all in `build_alignment.py`, all passing)

- every `words` row appears exactly once as `hebrew_word_id`: 264,217 ✓
- base rows == words count ✓
- every `kjv_words` row referenced exactly once: 610,324 ✓
- every `ylt_renderings` row referenced exactly once: 337,601 ✓
- `seq` dense 1..N per verse, zero gaps/violations ✓
- `PRAGMA foreign_key_check` clean ✓
- Total: 836,290 rows across 23,354 verses.
- Idempotence: three consecutive runs; runs 2 and 3 produce byte-identical
  table content (SHA-256
  `a15a556aafa25b7668d84593ca0b40e00e0dd782cef1c65edfa890f2500c5ed4`
  over all columns ordered by `alignment_id`).

## 9. Known limitations (heuristic, not parse — read before using roles)

1. **Construct chains / genitives unresolved:** bare nouns default to
   subject, so genitives read as subjects (מִצְרַיִם "of Egypt",
   עֲבָדִים "of bondage" in Ex 20:2; הַמֹּרִיָּה/הֶהָרִים in Gen 22:2).
2. **Unsplit bound prepositions:** OSHB does not split maqqef-bound
   אֶל־/עַל־/בְּ־ (אֶל־אֶרֶץ, עַל־יְהוּדָה, בְּכָל־לִבֶּךָ "with all your
   heart"); these label `subject` instead of `prepositional-phrase`.
   (Bound **את־** *is* handled via surface text, §7.)
3. **Adverbial accusatives** label `subject` (אֲרָמִית "in Aramaic",
   Dan 2:4).
4. **Verbless clauses:** every bare noun is a provisional subject; no
   predicate/subject distinction (Deut 6:4: all four nouns subject,
   אֶחָד qualifier:adj — morph-honest).
5. **Participles/infinitives** count as verbs (רֹעִי "my shepherd",
   Ps 23:1 — labeled verb by heuristic).
6. **Apposition, fronting, subordinate clauses, poetry** are not resolved.
7. **Source-parse limits inherited:** קַח־נָא is one word row keyed
   H4994/`HTe` (verb unrecoverable from morph); 4,921 KJV renderings point
   outside the Hebrew word's verse; Gen 1:1's את row carries renderings
   "created"/"and" because KJV word 5 ("created") bears the composite
   Strong's `H0853,H01254`.
8. Aramaic לְ־ accusatives will read as prepositional phrases (§7).

## 10. Strong's composites — what this table does and does not resolve

Each `words` row already carries **one exact raw Strong's string**
(e.g. `H0853,H01254` on KJV "created", Gen 1:1). `word_alignment` links
the **whole Hebrew word row**, so that attribute stays intact and exact —
composite strings remain source annotations and are **not** split into
multiple alignment identities. Component→standalone-Strong's foreign keys
are therefore unnecessary for this word-level alignment. In Kit's terms:
the table resolves identity at the **word/alignment level** (which Hebrew
word, which KJV word, which YLT rendering belong together, with a unique
`alignment_id`), not at the lexical-component level. The composite
question — how `H0853,H01254` decomposes — is preserved as raw data for
that later analysis, not pre-answered here.

## 11. Hand-check verses (printed by every build)

Gen 1:1 · Ps 23:1 · Ex 20:2 · Dan 2:4 · Gen 22:2 · Isa 1:1 · Prov 3:5 ·
Deut 6:4 · Gen 4:9 · Gen 31:55 (English-only versification → all KJV rows
`translator-supplied` satellites). Full output in the build log.

## 12. Provenance / divergence

Built 2026-09-28 from the local `~/workspace/bible-project/bible_v2.db`.
**This local database now diverges from the laptop staging copy**: it
contains the additive `word_alignment` table (plus its two indexes) that
staging lacks. Re-shipping the database belongs with the other pending
corrections already queued — live cutover has since occurred (2026-09-28 ~17:15 PDT), so re-shipping now updates the live laptop copy. The builder is
idempotent: re-running `python3 build_alignment.py` drops and rebuilds
only `word_alignment`.
