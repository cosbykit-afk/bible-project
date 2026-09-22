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

CREATE TABLE translation_choice(
  choice_id     INTEGER PRIMARY KEY,
  translation_id INTEGER NOT NULL REFERENCES translation(translation_id)
    ON DELETE CASCADE,
  word_id       INTEGER NOT NULL,  -- -> bible.db.words(word_id), app-enforced
  chosen_source TEXT NOT NULL CHECK(chosen_source IN ('kjv','ylt','other')),
  chosen_text   TEXT NOT NULL,
  updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(translation_id, word_id)
);
CREATE INDEX idx_choice_translation ON translation_choice(translation_id);
