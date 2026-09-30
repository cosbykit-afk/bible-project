#!/usr/bin/env python3
"""Merge textual-variant support into word_variants (Kit 2026-09-30).

Kit's decision: the two word_variants definitions (build_variants.py's
spelling-variance table and schema_var_notes.sql's textual-variant table)
merge into ONE table, with variant_kind tagging the kind of variant.

Migration: adds the variant_kind discriminator plus the textual-variant
columns (variant_text, witness, variant_type) and created_at. Every existing
row is spelling-kind (backfilled variant_kind='spelling'); no existing column
value is touched.

Method: build the merged table under a temp name, copy rows, verify, swap.
Idempotent: re-running on an already-merged table is a verified no-op.

Usage: python3 migrate_variants_merge.py --db bible_v2.db [--dry-run]
"""
import argparse
import sqlite3
import sys

MERGED_DDL = """
CREATE TABLE word_variants_new(
  word_id      INTEGER NOT NULL REFERENCES words(word_id),
  variant_seq  INTEGER NOT NULL,
  variant_kind TEXT NOT NULL CHECK (variant_kind IN ('spelling','textual')),
  unpointed    TEXT NOT NULL,
  letters      TEXT NOT NULL,
  variant_text TEXT,         -- textual kind: pointed variant reading (NULL for spelling)
  convention   TEXT,          -- spelling kind: 'v1-medial' | 'academic-final'
  source       TEXT,          -- spelling kind: 'v1-stored' | 'oshb-verbatim' |
                              --   'transduced-from-v1' | 'conjectural'
                              --   (NULL for textual: provenance is witness)
  witness      TEXT,          -- textual kind: manuscript siglum ('LXX','DSS','SP',...)
  variant_type TEXT,          -- textual kind: 'orthographic' | 'substantive' | ...
  basis        TEXT,          -- evidence note / rule citation
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(word_id, variant_seq)
)
"""

OLD_COLS = ["word_id", "variant_seq", "unpointed", "letters",
            "convention", "source", "basis"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(word_variants)")]
    if "variant_kind" in cols:
        print("word_variants already merged (variant_kind present); no-op.")
        return 0
    for c in OLD_COLS:
        if c not in cols:
            print("FATAL: expected column %s missing; aborting" % c)
            return 1

    n_before = cur.execute("SELECT COUNT(*) FROM word_variants").fetchone()[0]
    print("rows before: %d" % n_before, flush=True)

    if args.dry_run:
        print("dry-run: would rebuild word_variants with merged schema; "
              "%d rows backfilled variant_kind='spelling'." % n_before)
        return 0

    cur.execute("DROP TABLE IF EXISTS word_variants_new")
    cur.execute(MERGED_DDL)
    cur.execute("""
        INSERT INTO word_variants_new
          (word_id, variant_seq, variant_kind, unpointed, letters,
           variant_text, convention, source, witness, variant_type, basis)
        SELECT word_id, variant_seq, 'spelling', unpointed, letters,
               NULL, convention, source, NULL, NULL, basis
        FROM word_variants
    """)
    # ---- verification before the swap ----
    n_new = cur.execute("SELECT COUNT(*) FROM word_variants_new").fetchone()[0]
    assert n_new == n_before, (n_new, n_before)
    n_spell = cur.execute(
        "SELECT COUNT(*) FROM word_variants_new "
        "WHERE variant_kind='spelling'").fetchone()[0]
    assert n_spell == n_before, n_spell
    n_dup = cur.execute("""
        SELECT COUNT(*) FROM (
          SELECT word_id, variant_seq, COUNT(*) c FROM word_variants_new
          GROUP BY word_id, variant_seq HAVING c > 1)""").fetchone()[0]
    assert n_dup == 0, n_dup
    diff = cur.execute("""
        SELECT COUNT(*) FROM (
          SELECT word_id, variant_seq, unpointed, letters, convention, source, basis
          FROM word_variants
          EXCEPT
          SELECT word_id, variant_seq, unpointed, letters, convention, source, basis
          FROM word_variants_new)
        UNION ALL
        SELECT COUNT(*) FROM (
          SELECT word_id, variant_seq, unpointed, letters, convention, source, basis
          FROM word_variants_new
          EXCEPT
          SELECT word_id, variant_seq, unpointed, letters, convention, source, basis
          FROM word_variants)""").fetchall()
    assert all(r[0] == 0 for r in diff), diff
    n_fk = cur.execute("PRAGMA foreign_key_check").fetchall()
    assert not n_fk, n_fk[:3]
    print("pre-swap verification: %d rows, all spelling, 0 old-column diffs, "
          "0 FK violations." % n_new, flush=True)

    cur.execute("DROP TABLE word_variants")
    cur.execute("ALTER TABLE word_variants_new RENAME TO word_variants")
    cur.execute("CREATE INDEX idx_variants_word ON word_variants(word_id)")
    cur.execute("CREATE INDEX idx_variants_kind ON word_variants(variant_kind)")
    con.commit()

    # ---- post-swap verification ----
    n_after = cur.execute("SELECT COUNT(*) FROM word_variants").fetchone()[0]
    assert n_after == n_before, (n_after, n_before)
    kinds = cur.execute(
        "SELECT DISTINCT variant_kind FROM word_variants").fetchall()
    assert kinds == [("spelling",)], kinds
    print("merged: %d rows, kinds=%s." % (n_after, kinds))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
