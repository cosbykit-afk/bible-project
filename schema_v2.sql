-- Bible database v2 — normalized schema.
-- Built by migrate_v2.py from bible.db (v1). Design rationale: schema_v2.md.
-- Every FK declared and enforced. Conventions:
--   * book_id 1..39 preserved from v1 book_num (stable natural key).
--   * strongs keeps its stable TEXT form ('H7225') as PK.
--   * word_id values preserved from v1 (translation choice files index by word_id).
--   * Pure derivations (root_code, book/chapter/verse on word rows) live in
--     views, not tables. unpointed/letters are preserved verbatim from v1
--     (the migration does not adjudicate legacy values).

PRAGMA foreign_keys=ON;

CREATE TABLE books(
  book_id   INTEGER PRIMARY KEY,   -- 1..39, was book_num
  name_en   TEXT NOT NULL,
  name_he   TEXT NOT NULL
);

CREATE TABLE verses(
  verse_id  INTEGER PRIMARY KEY,
  book_id   INTEGER NOT NULL REFERENCES books(book_id),
  chapter   INTEGER NOT NULL,
  verse     INTEGER NOT NULL,
  UNIQUE(book_id, chapter, verse)
);
-- verses = UNION of (book,chapter,verse) from words, ylt_verses, kjv_words,
-- so the 139 English-versification orphans (e.g. Gen 31:55 = Heb 32:1) resolve.

CREATE TABLE strongs(
  strongs   TEXT PRIMARY KEY,       -- 'H7225', or a composite 'H01,H015' verbatim
  language  TEXT NOT NULL           -- 'H' (all H in this corpus; schema allows 'A')
);

-- Relational decomposition of composite Strong's values ('H01,H015').
-- The exact original string (and component order) is preserved here;
-- strongs.strongs keeps the verbatim composite. Components are NOT a hard
-- FK to strongs: 155 components (e.g. 'H010') have no row of their own.
CREATE TABLE strongs_components(
  strongs   TEXT NOT NULL REFERENCES strongs(strongs),
  seq       INTEGER NOT NULL,        -- 0-based component order
  component TEXT NOT NULL,           -- e.g. 'H01', verbatim
  PRIMARY KEY(strongs, seq)
);

CREATE TABLE strongs_sources(
  source_id INTEGER PRIMARY KEY,
  source    TEXT NOT NULL UNIQUE    -- 'oshb', 'oshb-split', 'kit'
);

CREATE TABLE morph_patterns(
  pattern_id   INTEGER PRIMARY KEY,
  pattern      TEXT NOT NULL UNIQUE,  -- OSHB @morph verbatim, e.g. 'HR/Ncfsa'
  language     TEXT,                  -- 'H' / 'A' (first char)
  parse_status TEXT NOT NULL DEFAULT 'parsed',  -- 'parsed' | 'unparsed'
  parse_notes  TEXT
);
-- 79 words have no morph: their morph_pattern_id is NULL (documented, kept).

CREATE TABLE morph_segments(
  segment_id INTEGER PRIMARY KEY,
  pattern_id INTEGER NOT NULL REFERENCES morph_patterns(pattern_id),
  seq        INTEGER NOT NULL,       -- 0-based, '/' split order
  code       TEXT NOT NULL,          -- segment code verbatim, e.g. 'Ncfsa'
  pos        TEXT,                   -- A C D N P R S T V
  pos_name   TEXT,
  stem       TEXT,  stem_name TEXT,   -- verbs
  conj       TEXT,  conj_name TEXT,   -- verbs: conjugation
  type       TEXT,  type_name TEXT,   -- adjectives/nouns/pronouns/preps/suffixes/particles
  person     TEXT,                   -- 1/2/3/x
  person_name TEXT,
  gender     TEXT,                   -- b/c/f/m/x
  gender_name TEXT,
  number     TEXT,                   -- d/p/s/x
  number_name TEXT,
  state      TEXT,                   -- a/c/d
  state_name TEXT,
  UNIQUE(pattern_id, seq)
);
-- COMPUTED parse of OSHB morphology codes per the authoritative doc
-- (openscriptures.github.io/morphhb/parsing/HebrewMorphologyCodes.html,
-- fetched 2026-09-28; CC-BY-4.0). Any segment with a code letter outside the
-- documented sets flags its pattern parse_status='unparsed'.

CREATE TABLE words(
  word_id           INTEGER PRIMARY KEY,  -- stable from v1
  orig_word_id      TEXT,                -- import natural key; NOT unique in v1
                                       -- (3 source ids each map to 2 word rows:
                                       --  split/merged tokens 51399, 252785, 227963)
  verse_id          INTEGER NOT NULL REFERENCES verses(verse_id),
  word_pos          INTEGER NOT NULL,
  pointed           TEXT NOT NULL,        -- canonical surface form (source)
  unpointed         TEXT,                 -- PRESERVED VERBATIM from v1
                                         -- (candidate derivation in migrate_v2.py
                                         -- for review only; NOT applied)
  letters           TEXT,                 -- PRESERVED VERBATIM from v1 (same)
  strongs           TEXT REFERENCES strongs(strongs),  -- NULL: 6,008 words
  strongs_source_id INTEGER REFERENCES strongs_sources(source_id),  -- NULL iff strongs NULL
  morph_pattern_id  INTEGER REFERENCES morph_patterns(pattern_id),   -- NULL: 79 words
  is_aramaic        INTEGER NOT NULL DEFAULT 0,
  root_id           INTEGER NOT NULL REFERENCES root_entry(root_id),
  root_form_seq     INTEGER NOT NULL,
  root_vowel_seq    INTEGER NOT NULL,
  FOREIGN KEY(root_id, root_form_seq) REFERENCES root_form(root_id, form_seq),
  FOREIGN KEY(root_id, root_form_seq, root_vowel_seq)
    REFERENCES root_vowel(root_id, root_form_seq, vowel_seq),
  UNIQUE(verse_id, word_pos),
  CHECK((strongs IS NULL) = (strongs_source_id IS NULL))
);

CREATE TABLE root_entry(
  root_id    INTEGER PRIMARY KEY,
  root       TEXT NOT NULL UNIQUE,
  word_count INTEGER NOT NULL   -- build-maintained cached aggregate
);

CREATE TABLE root_form(
  root_id         INTEGER NOT NULL REFERENCES root_entry(root_id),
  form_seq        INTEGER NOT NULL,
  prefix1         TEXT, prefix2 TEXT, prefix3 TEXT,
  suffix1         TEXT, suffix2 TEXT,
  prefix1_disp    TEXT, prefix2_disp TEXT, prefix3_disp TEXT,  -- MOVED from words (FD-verified)
  suffix1_disp    TEXT, suffix2_disp TEXT,
  word_count      INTEGER NOT NULL,  -- build-maintained cached aggregate
  example_pointed TEXT,
  example_unpointed TEXT,
  PRIMARY KEY(root_id, form_seq)
);

CREATE TABLE root_vowel(
  root_id       INTEGER NOT NULL,
  root_form_seq INTEGER NOT NULL,
  vowel_seq     INTEGER NOT NULL,
  vowel_pattern TEXT NOT NULL,
  word_count    INTEGER NOT NULL,  -- build-maintained cached aggregate
  PRIMARY KEY(root_id, root_form_seq, vowel_seq),
  FOREIGN KEY(root_id, root_form_seq) REFERENCES root_form(root_id, form_seq)
);

-- Lexicon: header + normalized children (were 4 multi-value TEXT blobs).
CREATE TABLE lexicon(
  root_id       INTEGER NOT NULL,
  root_form_seq INTEGER NOT NULL,
  vowel_seq     INTEGER NOT NULL,
  PRIMARY KEY(root_id, root_form_seq, vowel_seq),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES root_vowel(root_id, root_form_seq, vowel_seq)
);
CREATE TABLE lexicon_kjv_rendering(
  root_id INTEGER NOT NULL, root_form_seq INTEGER NOT NULL, vowel_seq INTEGER NOT NULL,
  seq     INTEGER NOT NULL,          -- preserves the build's frequency order
  rendering TEXT NOT NULL,
  PRIMARY KEY(root_id, root_form_seq, vowel_seq, seq),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES lexicon(root_id, root_form_seq, vowel_seq)
);
CREATE TABLE lexicon_ylt_rendering(
  root_id INTEGER NOT NULL, root_form_seq INTEGER NOT NULL, vowel_seq INTEGER NOT NULL,
  seq     INTEGER NOT NULL,
  rendering TEXT NOT NULL,
  PRIMARY KEY(root_id, root_form_seq, vowel_seq, seq),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES lexicon(root_id, root_form_seq, vowel_seq)
);
CREATE TABLE lexicon_ylt_context(
  root_id INTEGER NOT NULL, root_form_seq INTEGER NOT NULL, vowel_seq INTEGER NOT NULL,
  seq      INTEGER NOT NULL,
  verse_id INTEGER NOT NULL REFERENCES verses(verse_id),
  context_text TEXT NOT NULL,         -- the YLT verse text for that verse
  PRIMARY KEY(root_id, root_form_seq, vowel_seq, seq),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES lexicon(root_id, root_form_seq, vowel_seq)
);
CREATE TABLE lexicon_found_verse(
  root_id INTEGER NOT NULL, root_form_seq INTEGER NOT NULL, vowel_seq INTEGER NOT NULL,
  verse_id INTEGER NOT NULL REFERENCES verses(verse_id),
  PRIMARY KEY(root_id, root_form_seq, vowel_seq, verse_id),
  FOREIGN KEY(root_id, root_form_seq, vowel_seq)
    REFERENCES lexicon(root_id, root_form_seq, vowel_seq)
);

CREATE TABLE glosses(
  strongs TEXT NOT NULL REFERENCES strongs(strongs),
  source  TEXT NOT NULL,              -- 'bdb' | 'strongs_he'
  gloss   TEXT NOT NULL,
  PRIMARY KEY(strongs, source)
);

CREATE TABLE kjv_words(
  kjv_word_id INTEGER PRIMARY KEY,
  verse_id    INTEGER NOT NULL REFERENCES verses(verse_id),
  kjv_pos     INTEGER NOT NULL,
  kjv_word    TEXT NOT NULL,
  strongs     TEXT REFERENCES strongs(strongs),  -- NULL: 40,741 rows
  UNIQUE(verse_id, kjv_pos)
);

CREATE TABLE kjv_renderings(
  rendering_id INTEGER PRIMARY KEY,
  word_id      INTEGER NOT NULL REFERENCES words(word_id),
  kjv_word     TEXT NOT NULL,
  kjv_strongs  TEXT REFERENCES strongs(strongs),
  method       TEXT NOT NULL          -- 'direct' | 'maqqef-component' | 'verse-remap'
);
CREATE INDEX idx_kjv_renderings_word ON kjv_renderings(word_id);

CREATE TABLE ylt_verses(
  verse_id INTEGER PRIMARY KEY REFERENCES verses(verse_id),
  text     TEXT NOT NULL
);

CREATE TABLE ylt_renderings(
  rendering_id INTEGER PRIMARY KEY,
  word_id      INTEGER NOT NULL REFERENCES words(word_id),
  ylt_word     TEXT NOT NULL,
  ylt_word_pos INTEGER NOT NULL,
  label        TEXT NOT NULL          -- 'bridged' (computed alignment)
);
CREATE INDEX idx_ylt_renderings_word ON ylt_renderings(word_id);
CREATE INDEX idx_words_orig ON words(orig_word_id);
CREATE INDEX idx_words_verse ON words(verse_id);
CREATE INDEX idx_words_strongs ON words(strongs);
CREATE INDEX idx_words_morph ON words(morph_pattern_id);
CREATE INDEX idx_words_root ON words(root_id, root_form_seq, root_vowel_seq);
CREATE INDEX idx_kjv_words_verse ON kjv_words(verse_id);

-- ============================================================================
-- DERIVED-DATA STAGE (built after migrate_v2.py; not part of the base migration).
-- Build order: migrate_v2.py -> build_alignment.py -> build_variants.py
-- These tables record analysis/variance; they never alter base tables.
-- ============================================================================

CREATE TABLE word_alignment(
  alignment_id   INTEGER PRIMARY KEY,
  verse_id       INTEGER NOT NULL REFERENCES verses(verse_id),
  seq            INTEGER NOT NULL,
  hebrew_word_id INTEGER REFERENCES words(word_id),
  kjv_word_id    INTEGER REFERENCES kjv_words(kjv_word_id),
  ylt_rendering_id INTEGER REFERENCES ylt_renderings(rendering_id),
  syntactic_role TEXT NOT NULL,
  role_basis     TEXT NOT NULL,
  UNIQUE(verse_id, seq)
);
CREATE INDEX idx_alignment_hebrew ON word_alignment(hebrew_word_id);
CREATE INDEX idx_alignment_verse ON word_alignment(verse_id, seq);

CREATE TABLE word_variants(
  word_id     INTEGER NOT NULL REFERENCES words(word_id),
  variant_seq INTEGER NOT NULL,
  unpointed   TEXT NOT NULL,
  letters     TEXT NOT NULL,
  convention  TEXT NOT NULL,   -- 'v1-medial' | 'academic-final'
  source      TEXT NOT NULL,   -- 'v1-stored' | 'oshb-verbatim' |
                               -- 'transduced-from-v1' | 'conjectural'
  basis       TEXT,            -- evidence note / rule citation
  PRIMARY KEY(word_id, variant_seq)
);
CREATE INDEX idx_variants_word ON word_variants(word_id);
