-- One-to-many tables for textual variants (Var) and scholarly notes (Notes)
-- Per Kit 2026-09-29: "definitely a one to many relationship"
-- Resolves U-4: Var/Notes are not single columns but related tables

-- Textual variants: one word can have many variant readings.
-- MERGED 2026-09-30 (Kit's decision): textual variants live in the unified
-- word_variants table (schema_v2.sql) with variant_kind='textual', NOT in a
-- separate table. The earlier standalone definition below is superseded; it is
-- kept here as the column-origin record for the textual kind.
--
-- Column mapping into merged word_variants:
--   variant_text            -> variant_text (pointed reading; NULL for spelling rows)
--   variant_text_unpointed  -> unpointed
--   witness                 -> witness
--   variant_type            -> variant_type
-- (variant_id is superseded by the merged PRIMARY KEY(word_id, variant_seq);
--  textual rows continue variant_seq per word after the spelling rows.)
-- Superseded definition (do not apply):
-- CREATE TABLE IF NOT EXISTS word_variants (
--     variant_id INTEGER PRIMARY KEY,
--     word_id INTEGER NOT NULL REFERENCES words(word_id),
--     variant_text TEXT NOT NULL,
--     variant_text_unpointed TEXT,
--     witness TEXT,
--     variant_type TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Scholarly notes: one word can have many notes
CREATE TABLE IF NOT EXISTS word_notes (
    note_id INTEGER PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES words(word_id),
    note_text TEXT NOT NULL,              -- the note content
    note_type TEXT,                       -- textual, lexical, grammatical, etc.
    source TEXT,                          -- scholarly source if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_word_notes_word_id ON word_notes(word_id);
CREATE INDEX IF NOT EXISTS idx_word_notes_type ON word_notes(note_type);
