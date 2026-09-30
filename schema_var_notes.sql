-- One-to-many tables for textual variants (Var) and scholarly notes (Notes)
-- Per Kit 2026-09-29: "definitely a one to many relationship"
-- Resolves U-4: Var/Notes are not single columns but related tables

-- Textual variants: one word can have many variant readings
CREATE TABLE IF NOT EXISTS word_variants (
    variant_id INTEGER PRIMARY KEY,
    word_id INTEGER NOT NULL REFERENCES words(word_id),
    variant_text TEXT NOT NULL,           -- the variant reading (Hebrew)
    variant_text_unpointed TEXT,          -- unpointed form for matching
    witness TEXT,                         -- manuscript/source siglum (e.g. LXX, DSS, SP)
    variant_type TEXT,                    -- orthographic, substantive, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_word_variants_word_id ON word_variants(word_id);
CREATE INDEX IF NOT EXISTS idx_word_variants_witness ON word_variants(witness);

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
