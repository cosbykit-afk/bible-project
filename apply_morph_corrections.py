#!/usr/bin/env python3
"""Apply academically-researched morphology corrections (item .4).

Source: morphology_research.md (2026-09-28), findings-only research against
the morphhb documentation, BDB's Biblical Aramaic appendix, Gzella, Marshall.

What this does:
  ESTABLISHED (9 tokens): re-points words.morph_pattern_id to the corrected
    pattern row. 5x AT -> ATr (the migration's "unparsed" verdict was a
    misreading; the doc defines r = relative, and 165 other די tokens are ATr).
    4x Dan 5:25 writing-on-the-wall nouns -> ANcmsa / AC/ANcmpa (BDB genders).
  PROBABLE (3 tokens, Dan 5:26-28): words KEEP their ANxxxa pattern; the
    probable ANcmsa reading is staged in morph_variants, not applied.
  SECONDARY readings (participle re-reading AVQsmsa; gentilic AC/ANgmpa):
    staged in morph_variants only, never assigned to words.

Every touched word gets morph_variants rows: seq 1 = legacy v1 code,
seq 2 = corrected/probable code, seq 3 = secondary reading where one exists.
The table documents variance; absence of a row means the v1 reading stands
unchallenged.

Idempotent: re-running re-verifies preconditions, re-points (no-op if already
correct), and rebuilds variant rows for exactly these 12 word_ids.
Creates the AC/ANcmpa pattern row + segments if missing (copied from the
existing AC/Ncmpa composite structure).
"""
import sqlite3, sys, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_v2.db")
SRC = "morphology-research-2026-09-28"

# word_id -> (current_code, new_code_or_None, confidence, basis)
ESTABLISHED_AT = {
    247986: ("AT", "ATr", "established",
             "doc Particle types: r = relative; 165x corpus precedent (96 genitive); Gzella: די connects genitive 'A of B'"),
    248141: ("AT", "ATr", "established",
             "doc Particle types: r = relative; 165x corpus precedent (96 genitive); Gzella: די connects genitive 'A of B'"),
    248235: ("AT", "ATr", "established",
             "doc Particle types: r = relative; 165x corpus precedent (96 genitive); Gzella: די connects genitive 'A of B'"),
    248457: ("AT", "ATr", "established",
             "doc Particle types: r = relative; 165x corpus precedent (96 genitive); Gzella: די connects genitive 'A of B'"),
    248465: ("AT", "ATr", "established",
             "doc Particle types: r = relative; 165x corpus precedent (96 genitive); Gzella: די connects genitive 'A of B'"),
}
ESTABLISHED_NOUN = {
    248840: ("ANxxxa", "ANcmsa", "established", "BDB n.[m.] 'mina'; sg.; abs."),
    248841: ("ANxxxa", "ANcmsa", "established", "BDB n.[m.] 'mina'; sg.; abs."),
    248842: ("ANxxxa", "ANcmsa", "established", "BDB n.[m.] 'shekel'; sg.; abs."),
    248843: ("AC/Nxxxa", "AC/ANcmpa", "established",
             "BDB n.[m.] 'half-mina'; ־ִין = m.pl.abs. (Marshall); dual nonexistent in Biblical Aramaic; type=c probable"),
}
# word_id -> (probable_code, secondary_code_or_None, basis_probable, basis_secondary)
PROBABLE = {
    248846: ("ANcmsa", "AVQsmsa",
             "noun-label per MT pointing + OSHB POS + label/verb structure; participle re-reading is the live alternative",
             "passive-participle re-reading ('numbered'); formally identical for מנא; secondary as annotation of the MT as pointed"),
    248850: ("ANcmsa", "AVQsmsa",
             "noun-label per MT pointing + OSHB POS + label/verb structure; MT pointing (tsere) excludes participle vocalization תקיל",
             "passive-participle re-reading ('weighed'); implies re-vocalized תקיל (cf. תקילתה); secondary as annotation of the MT as pointed"),
    248855: ("ANcmsa", "AVQsmsa",
             "BDB 'prob. n.[m.]'; same structure; MT pointing excludes פריס",
             "passive-participle re-reading ('divided'); implies re-vocalized פריס (cf. פריסת); secondary as annotation of the MT as pointed"),
}
SECONDARY_EXTRA = {
    248843: ("AC/ANgmpa", "secondary",
             "gentilic wordplay on פרסין: 'Persians' (cf. 5:28 ופרס; BDB s.v. פרס n.pr.terr. et gent.); probable secondary reading"),
}

DDL = """
CREATE TABLE IF NOT EXISTS morph_variants(
  word_id    INTEGER NOT NULL REFERENCES words(word_id),
  variant_seq INTEGER NOT NULL,
  morph_code TEXT NOT NULL,
  pattern_id INTEGER REFERENCES morph_patterns(pattern_id),
  confidence TEXT NOT NULL,   -- legacy | established | probable | secondary
  source     TEXT NOT NULL,   -- v1-stored | morphology-research-2026-09-28
  basis      TEXT,
  PRIMARY KEY(word_id, variant_seq)
);
CREATE INDEX IF NOT EXISTS idx_morph_variants_word ON morph_variants(word_id);
"""

def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()
    cur.executescript(DDL)

    def pat_id(code):
        r = cur.execute("SELECT pattern_id FROM morph_patterns WHERE pattern=?", (code,)).fetchone()
        return r[0] if r else None

    # 1. ensure AC/ANcmpa pattern row + segments (copy AC/Ncmpa structure)
    if pat_id("AC/ANcmpa") is None:
        model = cur.execute("SELECT pattern_id FROM morph_patterns WHERE pattern='AC/Ncmpa'").fetchone()[0]
        segs = cur.execute(
            "SELECT seq, code, pos, pos_name, stem, stem_name, conj, conj_name, type, type_name,"
            " person, person_name, gender, gender_name, number, number_name, state, state_name"
            " FROM morph_segments WHERE pattern_id=? ORDER BY seq", (model,)).fetchall()
        cur.execute("INSERT INTO morph_patterns(pattern, language, parse_status, parse_notes)"
                    " VALUES('AC/ANcmpa','A','parsed','added by apply_morph_corrections.py; structure copied from AC/Ncmpa')")
        nid = cur.lastrowid
        for s in segs:
            cur.execute("INSERT INTO morph_segments(pattern_id, seq, code, pos, pos_name, stem, stem_name,"
                        " conj, conj_name, type, type_name, person, person_name, gender, gender_name,"
                        " number, number_name, state, state_name) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (nid,) + s)
        print(f"created pattern AC/ANcmpa as id {nid}")
    else:
        nseg = cur.execute("SELECT COUNT(*) FROM morph_segments WHERE pattern_id=?",
                           (pat_id("AC/ANcmpa"),)).fetchone()[0]
        assert nseg == 2, f"AC/ANcmpa segment count unexpected: {nseg}"
        print("pattern AC/ANcmpa present with 2 segments")

    # 2. verify preconditions + re-point established words
    rep = list(ESTABLISHED_AT.items()) + list(ESTABLISHED_NOUN.items())
    for wid, (cur_code, new_code, conf, basis) in rep:
        have = cur.execute(
            "SELECT mp.pattern FROM words w JOIN morph_patterns mp ON mp.pattern_id=w.morph_pattern_id"
            " WHERE w.word_id=?", (wid,)).fetchone()[0]
        npid = pat_id(new_code)
        assert npid is not None, f"target pattern {new_code} missing"
        if have == new_code:
            continue  # already applied (rerun)
        assert have == cur_code, f"word {wid}: expected {cur_code}, found {have}"
        cur.execute("UPDATE words SET morph_pattern_id=? WHERE word_id=?", (npid, wid))
    print(f"re-pointed {len(rep)} words (established)")

    # 3. verify probable words still on legacy pattern
    for wid in PROBABLE:
        have = cur.execute(
            "SELECT mp.pattern FROM words w JOIN morph_patterns mp ON mp.pattern_id=w.morph_pattern_id"
            " WHERE w.word_id=?", (wid,)).fetchone()[0]
        assert have == "ANxxxa", f"word {wid}: expected ANxxxa, found {have}"
    print(f"{len(PROBABLE)} probable words left on ANxxxa (not re-pointed)")

    # 4. rebuild variant rows for the 12 word_ids
    wids = sorted(set(list(ESTABLISHED_AT) + list(ESTABLISHED_NOUN) + list(PROBABLE)))
    cur.executemany("DELETE FROM morph_variants WHERE word_id=?", [(w,) for w in wids])
    rows = []
    def add(wid, seq, code, pid, conf, src, basis):
        rows.append((wid, seq, code, pid, conf, src, basis))
    for wid, (cur_code, new_code, conf, basis) in list(ESTABLISHED_AT.items()) + list(ESTABLISHED_NOUN.items()):
        add(wid, 1, cur_code, pat_id(cur_code), "legacy", "v1-stored",
            "code as stored in v1 / carried by the base migration")
        add(wid, 2, new_code, pat_id(new_code), conf, SRC, basis)
    for wid, (pcode, scode, pbasis, sbasis) in PROBABLE.items():
        add(wid, 1, "ANxxxa", pat_id("ANxxxa"), "legacy", "v1-stored",
            "code as stored in v1 / carried by the base migration")
        add(wid, 2, pcode, pat_id(pcode), "probable", SRC, pbasis)
        add(wid, 3, scode, None, "secondary", SRC, sbasis)
    for wid, (scode, sconf, sbasis) in SECONDARY_EXTRA.items():
        add(wid, 3, scode, None, sconf, SRC, sbasis)
    cur.executemany(
        "INSERT INTO morph_variants(word_id, variant_seq, morph_code, pattern_id, confidence, source, basis)"
        " VALUES(?,?,?,?,?,?,?)", rows)
    print(f"inserted {len(rows)} morph_variants rows for {len(wids)} words")

    # 5. verification
    assert cur.execute("SELECT COUNT(*) FROM morph_variants WHERE morph_code IS NULL OR confidence IS NULL").fetchone()[0] == 0
    fk = cur.execute("PRAGMA foreign_key_check").fetchall()
    assert not fk, fk
    dense = cur.execute(
        "SELECT word_id FROM (SELECT word_id, COUNT(*) c, MAX(variant_seq) m FROM morph_variants"
        " GROUP BY word_id) WHERE c != m").fetchall()
    assert not dense, dense
    print("verification: 0 NULLs, 0 FK violations, variant_seq dense per word")
    print("--- per-word report ---")
    for r in cur.execute(
        "SELECT w.word_id, v.chapter, v.verse, w.pointed, mp.pattern, mv.variant_seq, mv.morph_code, mv.confidence"
        " FROM morph_variants mv JOIN words w ON w.word_id=mv.word_id"
        " JOIN morph_patterns mp ON mp.pattern_id=w.morph_pattern_id"
        " JOIN verses v ON v.verse_id=w.verse_id ORDER BY w.word_id, mv.variant_seq"):
        print(r)
    con.commit()
    con.close()

if __name__ == "__main__":
    main()
