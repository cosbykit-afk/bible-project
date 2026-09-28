# Morphology Research — Unresolved Patterns vs. Academic Sources

**Date:** 2026-09-28
**Task:** Item .4 — research the unresolved morphology against academic sources.
**Constraint:** No database modifications were made. This is findings only.
**Scope:** 12 tokens in `bible_v2.db` — 5× bare particle `AT`, 7× noun-with-unknown-features `ANxxxa` / `AC/Nxxxa`. All are Biblical Aramaic, all in Daniel.

**Scoping convention (Kit's rule):** *established* = cited and verifiable; *probable* = supported by corpus/contextual evidence but with a live alternative; *undetermined* = cannot be determined — no guess offered.

---

## 1. Source re-read: the morphhb documentation

Refetched and read in full on 2026-09-28:
`https://openscriptures.github.io/morphhb/parsing/HebrewMorphologyCodes.html`

### 1.1 The `AT` verdict was wrong — the doc DOES define the code

The migration kept `AT` as `parse_status='unparsed'` on the theory that "the morphhb doc was read as defining no bare-particle code." That reading was incorrect. The **Particle types** table defines nine particle types, including:

| code | type |
|------|------|
| a | affirmation |
| d | definite article |
| e | exhortation |
| i | interrogative |
| j | interjection |
| m | demonstrative |
| n | negative |
| o | direct object marker |
| **r** | **relative** |

There is no "bare particle" category in the documentation — every particle carries a type letter. The 5 `AT` tokens are therefore not a documentation gap; they are **upstream annotation gaps** (a missing type letter in the OSHB source data). The correct code is determined below.

### 1.2 Note 5, exact wording

> "Use 'x' as a placeholder for unknown **or unnecessary** values, but only if there is a necessary value following it. For example, finite verbs (perfect, imperfect) have person, but non-finite verbs (participle, infinitive) do not."

Two distinct uses of `x` exist in the corpus:
- **x = unnecessary** (correct, keep): demonstrative pronouns (`APdxms`, `HPdxms`, …) — person is inapplicable to demonstratives, so `x` holds the slot before gender/number. Verified: `APdxms` parses as pronoun / demonstrative / person=x / masculine / singular. All 40 `Pdx__/Pfx__/Pix__/Prx__` patterns are of this kind and are **not** problems.
- **x = unknown** (genuine): only the two noun patterns `ANxxxa` (6 tokens) and `AC/Nxxxa` (1 token). These are the only patterns where `x` marks truly undetermined features.

### 1.3 State and number codes used below

State: `a` = absolute, `c` = construct, `d` = determined. Number: `s`/`p`/`d` = singular/plural/dual. Gender: `m`/`f`.

---

## 2. Findings, item 1: the 5 bare-`AT` tokens (דִּי, H1768)

### 2.1 The tokens

| word_id | ref | wp | pointed | context |
|---|---|---|---|---|
| 247986 | Dan 4:12 | 10 | דִּ֣י | בְּדִתְאָא **דִּי** בָרָא — "in the grass **of** the field" |
| 248141 | Dan 4:20 | 21 | דִּ֣י | same phrase |
| 248235 | Dan 4:26 | 6 | דִּ֥י | מַלְכוּתָא **דִּי** בָבֶל — "the kingdom **of** Babylon" |
| 248457 | Dan 5:5 | 5 | דִּ֣י | אֶצְבְּעָן **דִּי** יַד־אֱנָשׁ — "fingers **of** a man's hand" |
| 248465 | Dan 5:5 | 13 | דִּ֣י | הֵיכְלָא **דִּי** מַלְכָּא — "the palace **of** the king" |

All five are the **genitive** use of דִּי ("of"), noun + דִּי + noun.

### 2.2 Proposed code: `ATr` — established

**Evidence chain:**

1. **The documentation defines it.** Particle type `r` = relative (morphhb doc, Particle types table). `ATr` = Aramaic + particle + relative. No documentation change is needed.
2. **The corpus already uses it — 165 times.** Every other דִּי (H1768) token carrying a particle analysis in the database is coded `ATr` (165×). The 5 bare `AT` are the only exceptions.
3. **OSHB uses `r` for the genitive function too.** Of the 165 `ATr` tokens, **96 stand in genitive position** (directly followed by a noun), e.g. Ezra 4:10 בְּקִרְיָה **דִּי** שָׁמְרָיִן ("in the city **of** Samaria", `ATr`). The tagset has no separate "genitive particle" type; `r` covers both.
4. **Academic grammar confirms דִּי is one relative marker with both functions.** Gzella (*Imperial Aramaic* morphology §3, Tübingen): "The relative marker, zy (dy) /dī/ (in fact a fossilized genitive of older Semitic */ḏū/), **connects words in a genitive relationship ('A of B') and introduces relative as well as object clauses**." — https://tobias-lib.ub.uni-tuebingen.de/xmlui/bitstream/handle/10900/168831/Gzella_052.pdf?sequence=1&isAllowed=y
5. **Corroborating grammar.** Marshall (*The Aramaic Language*, biblicalstudies.org.uk): "Another peculiar but very frequent usage of דִּי is as a Paraphrase for the Genitive." — https://biblicalstudies.org.uk/pdf/e-books/marshall_j-t/aramaic-language_marshall.pdf
6. **Hebrew parallel.** Hebrew אֲשֶׁר (H834), the functional equivalent, is coded `HTr` 3,455× in the same corpus. The Aramaic relative particle takes the same `r`.

**Confidence: ESTABLISHED.** Proposed correction: `AT` → `ATr` for all 5 tokens. Basis: doc §Particle types (`r` = relative) + 165× corpus precedent (96 in genitive position) + Gzella.

### 2.3 Upstream accounting note (data fidelity, not a correction)

The pinned OSHB TSV (`worker-out/oshb/oshb_words.tsv`) contains **7** bare-`AT` annotations, but only 5 surface as `AT` words in the database. The other two were absorbed by maqaf-merging at ingest (pre-existing v1 tokenization, unchanged by the v2 migration):

- TSV Dan 5:5 wp 14 דִּֽי (`AT`, H1768) + wp 15 כְּתַל → DB word 11 **דִּֽי־כְתַל** (`ANcmsc`, H3797): the דִּי's particle morphology is dropped in the merge.
- TSV Dan 5:7 wp 27 דִֽי (`AT`, H1768) + wp 28 דַהֲבָא → DB word 25 **דִֽי־דַהֲבָא** (`ANcmsd/Td`, H1722): same absorption.

Both are genitive דִּי ("of the wall", "of gold"). If the variant apparatus (Kit's one-to-many instruction) is extended to morphology, these two merged tokens are candidates for a דִּי-particle variant row. Flagged here; no change made.

### 2.4 Audit: no other Aramaic particle is missing its type

A regex audit of all 3,437 patterns for bare `T` (particle with no following type letter, in any segment position) returns exactly one pattern: `AT`. The `Pdx__`-family `x` (person slot of demonstrative pronouns) is the legitimate "unnecessary value" use per doc note 5. **No other Aramaic — or Hebrew — particle code is incomplete.**

---

## 3. Findings, item 2: the 7 `Nxxxa` tokens (Dan 5:25–28, the writing on the wall)

### 3.1 The tokens

| word_id | ref | pointed | strongs | BDB gloss (local `glosses`, bdb source) |
|---|---|---|---|---|
| 248840 | Dan 5:25 wp 5 | מְנֵ֥א | H4484 | maneh; mina |
| 248841 | Dan 5:25 wp 6 | מְנֵ֖א | H4484 | maneh; mina |
| 248842 | Dan 5:25 wp 7 | תְּקֵ֥ל | H8625 | shekel; weigh |
| 248843 | Dan 5:25 wp 8 | וּפַרְסִֽין | H6537 | half-mina; break in two |
| 248846 | Dan 5:26 wp 3 | מְנֵ֕א | H4484 | maneh; mina |
| 248850 | Dan 5:27 wp 1 | תְּקֵ֑ל | H8625 | shekel; weigh |
| 248855 | Dan 5:28 wp 1 | פְּרֵ֑ס | H6537 | half-mina; break in two |

### 3.2 Why the noun analysis is correct for the MT as pointed

1. **The MT's pointing is the nominal (weights) vocalization throughout.** מְנֵא / תְּקֵל / פְּרֵס / פַּרְסִין are the weight-words: "mina, mina, shekel, and half-minas" (Dan 5:25). The verbal re-reading ("numbered, weighed, divided") requires *re-vocalization* — cf. the HUC/Hebrew Union College article on the riddle (IxTheo record 1650065892): "The first level represents scale weights, vocalized *mĕneʾ, tĕqēl, pĕrēs*, 'mina, shekel, half-mina' (**so the MT**). The second level represents actions of evaluation… vocalized *mĕnāh, tĕqal, pĕras*." — https://ixtheo.de/Record/1650065892
2. **The interpretation structure is label + inflected verb.** In 5:26–28 each word is quoted as a label and then interpreted with a *separately inflected* verb: מְנֵא → מְנָה ("has numbered"); תְּקֵל → תְּקִילְתָּה (`AVQi2ms`, "you were weighed"); פְּרֵס → פְּרִיסַת (`AVQp3fs`, "it [your kingdom, f.] is divided"). The label is the frozen nominal form.
3. **The strong-root forms exclude the participle pointing.** A Peil passive participle of the strong roots would be pointed תְּקִיל / פְּרִיס (hireq), as the interpretation's own תְּקִילְתָּה / פְּרִיסַת show. The MT's תְּקֵל / פְּרֵס (tsere) is the nominal pattern. (מְנֵא, from a ל״ה root, is formally ambiguous — see variants below.)
4. **OSHB's own POS is N** for all 7; only the features were left as `x`.

### 3.3 BDB gender evidence (verified 2026-09-28)

Source: Brown, Driver, Briggs, *A Hebrew and English Lexicon of the Old Testament* (1906), **Biblical Aramaic appendix** — verified in the OpenScriptures HebrewLexicon electronic edition (`BrownDriverBriggs.xml`, CC BY 4.0; BDB content public domain), Aramaic parts `xm`/`xq`/`xw`:

| entry | BDB headword | BDB analysis | gender |
|---|---|---|---|
| xm.al.ab | מְנֵא | **n.[m.]** maneh, mina, a weight | masculine |
| xw.ag.ab | תְּקֵל | **n.[m.]** shekel | masculine |
| xq.ae.ab | פְּרֵס | **prob. n.[m.]** half-mina | masculine (BDB marks the *nominal* reading "prob." — probably) |

(BDB's companion verb entries: מְנָה vb. "number, reckon"; פָּרַס n.pr.terr. et gent. "Persia, Persians" — the proper-noun homonym behind the "Persians" wordplay.)

### 3.4 Feature-by-feature determination

- **Type = common (`c`).** All three are common nouns (units of weight). Not proper names, not gentilics. (The "Persians" wordplay on פַּרְסִין is a secondary reading — see variants.)
- **Gender = masculine (`m`).** BDB: n.[m.] for all three headwords. Corroborated by form: Aramaic masculine nouns end in a consonant (Marshall, *The Aramaic Language*: "The Masc. has no distinctive ending. It invariably ends in a consonant, except in the Nouns derived from Verbs that end in ה or א").
- **Number.** Singular for מְנֵא / תְּקֵל / פְּרֵס (no plural morpheme). **Plural** for פַּרְסִין: ־ִין is the masculine plural absolute ending (Marshall: "the Masculine Nouns form their Plural in ־ִין"); the dual does not exist in Biblical Aramaic (Marshall: "two Numbers: Singular and Plural (the Dual not being found)"), and ־ִין (hireq-yod) is the plural shape, not dual ־ַיִן.
- **State = absolute (`a`).** None carries the determined-state ־ָא ending (contrast מַלְכָּא, determined); פַּרְסִין lacks determined ־ַיָּא. BDB's headwords are themselves the absolute forms.

### 3.5 Proposed corrections

| word_id | ref | form | current | proposed | confidence | basis |
|---|---|---|---|---|---|---|
| 248840 | Dan 5:25 | מְנֵא | ANxxxa | **ANcmsa** | established | BDB n.[m.] "mina"; sg.; abs. |
| 248841 | Dan 5:25 | מְנֵא | ANxxxa | **ANcmsa** | established | same |
| 248842 | Dan 5:25 | תְּקֵל | ANxxxa | **ANcmsa** | established | BDB n.[m.] "shekel"; sg.; abs. |
| 248843 | Dan 5:25 | וּפַרְסִין | AC/Nxxxa | **AC/ANcmpa** | established (features); type=c probable | BDB n.[m.] "half-mina"; ־ִין = m.pl.abs.; gentilic "Persians" wordplay is the known secondary reading |
| 248846 | Dan 5:26 | מְנֵא | ANxxxa | **ANcmsa** | probable | noun-label per MT pointing + OSHB POS + label/verb structure; participle re-reading is the live alternative (variant) |
| 248850 | Dan 5:27 | תְּקֵל | ANxxxa | **ANcmsa** | probable | same; MT pointing (tsere) excludes participle vocalization תְּקִיל |
| 248855 | Dan 5:28 | פְּרֵס | ANxxxa | **ANcmsa** | probable | BDB "prob. n.[m.]"; same structure; MT pointing excludes פְּרִיס |

### 3.6 Variant readings for the one-to-many apparatus (not corrections)

Per Kit's instruction, genuine alternatives belong in the variant relation, not in destructive re-tagging:

1. **Passive-participle re-reading (Dan 5:26–28).** Daniel's interpretation re-reads the three words verbally ("numbered, weighed, divided"). As a morphological variant: `AVQsmsa` (Aramaic, verb, peil stem `Q`, participle passive `s`, — no person per doc note 4 — masculine, singular, absolute). Note: for תְּקֵל/פְּרֵס this implies the re-vocalized forms תְּקִיל/פְּרִיס (cf. the interpretation's תְּקִילְתָּה, פְּרִיסַת); only מְנֵא is formally identical in both readings. Status: probable as an *interpretation*; secondary as an annotation of the MT as pointed.
2. **Gentilic wordplay on פַּרְסִין (Dan 5:25).** "Persians" (cf. 5:28 וּפָרָס, and BDB s.v. פָּרַס n.pr.terr. et gent.): variant type=gentilic, `AC/ANgmpa`. Status: probable secondary reading (the well-known double meaning of the inscription).

---

## 4. Summary counts

| category | count | status |
|---|---|---|
| `AT` → `ATr` (דִּי, genitive/relative particle) | 5 tokens | **resolved — established** |
| `ANxxxa` → `ANcmsa` (מְנֵא ×3, תְּקֵל ×2, פְּרֵס ×1) | 6 tokens | **resolved** — 4 established (5:25), 2 probable (5:27 תְּקֵל, 5:28 פְּרֵס); 5:26 מְנֵא probable |
| `AC/Nxxxa` → `AC/ANcmpa` (וּפַרְסִין) | 1 token | **resolved** — features established; type=c probable |
| Other bare-particle patterns in corpus | 0 | audit complete — none exist |
| Other `x`-as-unknown patterns | 0 | the 40 `Pdx__`-family patterns use `x` legitimately (unnecessary person on demonstratives, doc note 5) |
| **Undetermined** | **0** | nothing left unresolvable; the two maqaf-merged דִּי tokens are a tokenization observation, not a morphology question |

**Totals: 12 tokens examined — 9 resolved as established, 3 resolved as probable, 0 undetermined.**

Correction applied to none (per task constraint); the proposed-corrections tables in §2.2 and §3.5 are ready for implementation, and §3.6 lists the variant rows for the one-to-many apparatus.

---

## 5. What was NOT verified (honest gaps)

- **Rosenthal, *A Grammar of Biblical Aramaic*.** The standard reference (cited as such in the secondary literature surveyed) was not directly accessible in this session (archive.org copy is access-restricted; CAL was access-denied). The דִּי classification is instead established via Gzella (Tübingen, open access), Marshall (open access), the morphhb documentation, and 165× corpus precedent — convergent and sufficient, but a Rosenthal section citation (relative pronoun §§19–22 in the 1974/2006 eds.) remains a worthwhile follow-up for the final documentation.
- **HALOT** was not consulted (paywalled, per task instruction). BDB's Aramaic appendix sufficed for all three genders.
- The two maqaf-merged דִּי tokens (§2.3) inherit v1 tokenization; whether to surface their particle morphology as variant rows is a design decision for the variant-apparatus work, flagged but not resolved here.
