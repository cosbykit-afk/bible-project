-- website/app.db schema -- user and translation data only.
-- bible.db (corpus) is opened READ-ONLY; all writes go here.
-- word_id is a logical cross-database reference to bible.db.words(word_id),
-- enforced by application code (SQLite cannot enforce cross-db FKs).

CREATE TABLE app_user(
  user_id    INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE translation(
  translation_id INTEGER PRIMARY KEY,
  user_id        INTEGER NOT NULL REFERENCES app_user(user_id),
  name           TEXT NOT NULL,
  description    TEXT NOT NULL DEFAULT '',
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_translation_user ON translation(user_id);

-- Per-word choices are NOT rows here. Each translation gets a flat file
-- website/user_data/translation_<id>.choices: 264,217 bytes, one byte per word,
-- byte at offset (word_id - 1). The byte is the item number of the word's
-- drop-down that was selected: 0 = default (no choice); the rest index into
-- the word's drop-down list built as [KJV renderings | Young's renderings |
-- this translation's Other options]. "Other" is multi-value: each custom
-- rendering the user adds becomes a row below and a new drop-down item.
CREATE TABLE other_option(
  option_id     INTEGER PRIMARY KEY,
  translation_id INTEGER NOT NULL REFERENCES translation(translation_id)
    ON DELETE CASCADE,
  idx           INTEGER NOT NULL,  -- 1-based creation order within the translation
  text          TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(translation_id, idx)
);
CREATE INDEX idx_other_translation ON other_option(translation_id);
