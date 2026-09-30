#!/usr/bin/env python3
"""Build word_variants: one-to-many spelling variants per word_id.

Kit's ruling: the word ID stays single; spellings are multi-value, holding
alternate spellings, academic spellings, and outright word-choice variants.
This table records variance; it does not adjudicate between spellings.

Conventions:
  v1-medial     - v1 house convention: medial letter forms (no sofit),
                  hyphen-minus U+002D as maqaf
  academic-final - OSHB/WLC convention: final forms (sofit) at segment end,
                   maqaf U+05BE
Sources:
  v1-stored        - value copied verbatim from v1's words table
  oshb-verbatim    - resolution from anomaly_resolutions.json (OSHB audit);
                     v1conv rows are the same resolution rendered in v1 convention
  transduced-from-v1 - deterministic sofit/maqaf mapping applied to v1-stored
  conjectural      - explicitly conjectural reading (104753 only)

Rerunnable/idempotent: drops and rebuilds ONLY word_variants.
"""
import argparse
import json
import sqlite3
import sys

DEFAULT_DB = "/home/hatch/workspace/bible-project/bible_v2.db"
RES = "/home/hatch/workspace/bible-project/anomaly_resolutions.json"

# NOTE: task spec listed k/m/n/p only; tsade->final tsade added because
# Hebrew orthography requires it (3,298 segment-final tsade in corpus;
# omitting it would emit invalid academic spellings like ארצ for ארץ).
SOFIT = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}


def transduce_unpointed(s):
    """v1-medial unpointed -> academic-final: sofit at end-of-string or
    before hyphen-minus/maqaf, then hyphen-minus -> U+05BE maqaf."""
    chars = list(s or "")
    out = []
    for i, ch in enumerate(chars):
        if ch in SOFIT:
            nxt = chars[i + 1] if i + 1 < len(chars) else ""
            if nxt in ("", "-", "־"):
                out.append(SOFIT[ch])
                continue
        out.append(ch)
    return "".join(out).replace("-", "־")


def transduce_letters(transduced_unp):
    """Academic letters = academic unpointed with maqaf stripped (sofit
    forms preserved from segment-final positions, matching the audit's
    convention, e.g. לך־לכה־נא -> לךלכהנא)."""
    return transduced_unp.replace("־", "")


def evidence_basis(r):
    ev = r["evidence"]
    pos = ",".join(str(p) for p in ev["oshb_word_pos"])
    return ("OSHB {b} {ch}:{v} tokens {p} [{m}] | anomaly={a} | confidence={c}"
            .format(b=ev["oshb_book"], ch=ev["oshb_chapter"], v=ev["oshb_verse"],
                    p=pos, m=ev["match_method"], a=r["anomaly_class"],
                    c=r["confidence"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args()
    DB = args.db
    res = json.load(open(RES))
    anom = {int(k): v for k, v in res.items() if k != "_meta"}
    print("anomaly records: %d" % len(anom), flush=True)

    # ---- Step 0: verify transduction against the audit's v1conv forms ----
    up_mism, let_mism, let_flag = [], [], []
    for wid, r in sorted(anom.items()):
        t_u = transduce_unpointed(r["resolved_unpointed_v1conv"])
        if t_u != r["resolved_unpointed"]:
            up_mism.append(wid)
        # principled letters rule: strip maqaf from transduced unpointed
        if t_u.replace("־", "") != r["resolved_letters"]:
            let_mism.append(wid)
            let_flag.append(wid)
    print("unpointed round-trip mismatches (129): %d %s" % (len(up_mism), up_mism), flush=True)
    print("letters rule mismatches (129): %d %s" % (len(let_mism), let_mism), flush=True)
    if up_mism:
        print("FATAL: unpointed transduction failed verification; aborting", flush=True)
        sys.exit(1)
    # letters mismatches are audit-file inconsistencies, documented not fatal:
    # the file's values are stored verbatim with a FLAG in basis.

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()

    # ---- Step 1: rebuild (additive; no existing table touched) ----
    cur.execute("DROP TABLE IF EXISTS word_variants")
    cur.execute("""CREATE TABLE word_variants(
      word_id INTEGER NOT NULL REFERENCES words(word_id),
      variant_seq INTEGER NOT NULL,
      variant_kind TEXT NOT NULL CHECK (variant_kind IN ('spelling','textual')),
      unpointed TEXT NOT NULL,
      letters TEXT NOT NULL,
      variant_text TEXT,
      convention TEXT,
      source TEXT,
      witness TEXT,
      variant_type TEXT,
      basis TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(word_id, variant_seq)
    )""")
    cur.execute("CREATE INDEX idx_variants_word ON word_variants(word_id)")
    cur.execute("CREATE INDEX idx_variants_kind ON word_variants(variant_kind)")

    # ---- Step 2: populate ----
    rows = []
    weird_chars = set()
    n_normal = 0
    for wid, u, l in cur.execute(
            "SELECT word_id, unpointed, letters FROM words ORDER BY word_id"):
        u = u or ""
        l = l or ""
        for ch in u + l:
            if not ("\u0590" <= ch <= "\u05ff" or ch in "-־]"):
                weird_chars.add(ch)
        if wid in anom:
            r = anom[wid]
            b_ev = evidence_basis(r)
            rows.append((wid, 1, r["v1_unpointed"], r["v1_letters"],
                         "v1-medial", "v1-stored",
                         "v1 stored verbatim | anomaly=%s | confidence=%s"
                         % (r["anomaly_class"], r["confidence"])))
            rows.append((wid, 2, r["resolved_unpointed_v1conv"],
                         r["resolved_letters_v1conv"],
                         "v1-medial", "oshb-verbatim",
                         b_ev + " | rendered in v1 convention"))
            b3 = b_ev
            if wid in let_flag:
                b3 += (" | FLAG: file resolved_letters %s inconsistent with "
                       "resolved_unpointed %s (strip gives %s); stored verbatim"
                       % (r["resolved_letters"], r["resolved_unpointed"],
                          transduce_unpointed(
                              r["resolved_unpointed_v1conv"]).replace("־", "")))
            rows.append((wid, 3, r["resolved_unpointed"], r["resolved_letters"],
                         "academic-final", "oshb-verbatim", b3))
            if wid == 104753:
                rows.append((wid, 4, r["resolved_unpointed"],
                             r["resolved_letters"],
                             "academic-final", "conjectural",
                             "CONJECTURAL | medium confidence: v1 pointed "
                             "ככ־על corrupt; כי conjectured from OSHB "
                             "2 Samuel 18:20 כִּי־על"))
            if wid == 71448:
                rows.append((wid, 4, r["v1_unpointed"], r["v1_letters"],
                             "v1-medial", "v1-stored",
                             "TOKENIZATION ARTIFACT | phantom row from v1 split "
                             "of OSHB Joshua 9:7 tokens 12-14 (orig 71446.1); "
                             "stored value verified correct vs OSHB tokens "
                             "13-14; see word 71447"))
        else:
            n_normal += 1
            t_u = transduce_unpointed(u)
            t_l = transduce_letters(t_u)
            rows.append((wid, 1, u, l, "v1-medial", "v1-stored",
                         "v1 stored value, preserved verbatim"))
            rows.append((wid, 2, t_u, t_l, "academic-final",
                         "transduced-from-v1",
                         "deterministic sofit/maqaf mapping: כמנפצ→ךםןףץ at "
                         "segment end; hyphen-minus→U+05BE"))
    print("normal words: %d; unexpected chars in bulk input: %s"
          % (n_normal, sorted(weird_chars) if weird_chars else "none"), flush=True)
    cur.executemany(
        "INSERT INTO word_variants(word_id, variant_seq, variant_kind, unpointed, letters,"
        " convention, source, basis) VALUES (?,?,?,?,?,?,?,?)",
        [(wid, seq, "spelling", u, l, c, s, b)
         for (wid, seq, u, l, c, s, b) in rows])
    con.commit()
    print("inserted rows: %d" % len(rows), flush=True)

    # ---- Step 3: verification ----
    total = cur.execute("SELECT COUNT(*) FROM word_variants").fetchone()[0]
    print("total variant rows: %d" % total, flush=True)
    dist = cur.execute(
        "SELECT n, COUNT(*) FROM "
        "(SELECT word_id, COUNT(*) n FROM word_variants GROUP BY word_id) "
        "GROUP BY n ORDER BY n").fetchall()
    print("rows-per-word distribution: %s" % dist, flush=True)
    n_gt2 = cur.execute(
        "SELECT COUNT(*) FROM (SELECT word_id FROM word_variants "
        "GROUP BY word_id HAVING COUNT(*) > 2)").fetchone()[0]
    print("words with >2 variants: %d (expect 129)" % n_gt2, flush=True)
    nulls = cur.execute(
        "SELECT COUNT(*) FROM word_variants "
        "WHERE unpointed IS NULL OR letters IS NULL").fetchone()[0]
    print("NULL unpointed/letters: %d" % nulls, flush=True)
    gappy = cur.execute(
        "SELECT COUNT(*) FROM (SELECT word_id, COUNT(*) c, MAX(variant_seq) m "
        "FROM word_variants GROUP BY word_id HAVING c != m OR MIN(variant_seq) != 1)"
    ).fetchone()[0]
    print("words with non-dense variant_seq: %d" % gappy, flush=True)
    fk = cur.execute("PRAGMA foreign_key_check").fetchall()
    print("foreign_key_check violations: %d" % len(fk), flush=True)
    # every words row covered
    missing = cur.execute(
        "SELECT COUNT(*) FROM words w WHERE NOT EXISTS "
        "(SELECT 1 FROM word_variants v WHERE v.word_id = w.word_id)").fetchone()[0]
    print("words rows with zero variants: %d" % missing, flush=True)

    # spot check: 15 rows, mix of anomaly / maqaf-joined / plain / edge
    print("--- spot check ---", flush=True)
    for wid in [51400, 71447, 71448, 84266, 84702, 104753, 1, 2, 21988,
                121620, 231857, 231858, 100000, 200000, 264217]:
        pt = cur.execute(
            "SELECT pointed FROM words WHERE word_id=?", (wid,)).fetchone()[0]
        print("word %d pointed=%s" % (wid, pt[:40]), flush=True)
        for s, u, l, cv, src in cur.execute(
                "SELECT variant_seq, unpointed, letters, convention, source "
                "FROM word_variants WHERE word_id=? ORDER BY variant_seq",
                (wid,)):
            print("   seq%d [%s|%s] unp=%s let=%s" % (s, cv, src, u, l), flush=True)

    ok = (n_gt2 == 129 and nulls == 0 and gappy == 0 and not fk
          and missing == 0 and not up_mism)
    print("ALL VERIFICATIONS PASSED" if ok else "VERIFICATION FAILURES PRESENT",
          flush=True)
    con.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
