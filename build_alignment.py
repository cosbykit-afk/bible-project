#!/usr/bin/env python3
"""
build_alignment.py — build the word_alignment interlinear table in bible_v2.db.

Additive and rerunnable (idempotent): drops and rebuilds ONLY word_alignment;
no existing table is altered.

Model: one base row per Hebrew word (hebrew_word_id appears exactly once),
each carrying its primary KJV link (kjv_word_id) and primary YLT link
(ylt_rendering_id). Coverage satellites (hebrew_word_id NULL) are emitted for
every KJV word and every YLT rendering not covered by a base row, so that
every kjv_words row and every ylt_renderings row is referenced exactly once.

Per-verse ordering ("line upon line"): subjects, verbs, objects,
qualifier:adj, qualifier:adv, other, satellites, unresolved — seq dense 1..N.

Role assignment is a DETERMINISTIC morph+marker heuristic, not a syntactic
parse. See alignment_method.md for the full rule documentation, the
Gesenius-Kautzsch §117 citation for the את rule, and the labeled
heuristic-vs-established accounting.
"""
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible_v2.db")

REGION = {
    "subject": 1,
    "verb": 2,
    "object": 3,
    "qualifier:adj": 4,
    "qualifier:adv": 5,
    "other": 6,
    "translator-supplied": 7,   # satellites sort here too (region 7)
    "unresolved": 8,
}

# ----------------------------------------------------------------------------
# morphology head categories
# ----------------------------------------------------------------------------
# Head-finding: the lexical head is the LAST segment that is not a pure
# affix. Only C (conjunction) and S (pronominal suffix) are skipped -- a
# standalone R is a preposition (e.g. HR 'between'), a standalone T is a
# particle (e.g. HTr 'asher', HTn 'not'). Prefixes before the head are
# inspected for R (prepositional phrase) and T/o (object marker, e.g. the
# maqqef-bound marker in To+N compounds).


def load_pattern_heads(con):
    """pattern_id -> dict with:
         head_pos/head_type/head_type_name : last non-(C,S) segment (None if
             the pattern has no segments or only C/S segments)
         has_r_prefix  : an R (preposition) segment precedes the head
         et_prefix     : a T/o (object marker) segment precedes the head
         n_seg         : number of segments (0 for unparsed patterns)
    """
    segs = {}
    for pid, seq, pos, typ, tname in con.execute(
            "SELECT pattern_id, seq, pos, type, type_name FROM morph_segments "
            "ORDER BY pattern_id, seq"):
        segs.setdefault(pid, []).append((seq, pos, typ, tname))
    heads = {}
    for pid, lst in segs.items():
        core_idx = [i for i, (_, p, _, _) in enumerate(lst)
                    if p not in ("C", "S")]
        if core_idx:
            hi = core_idx[-1]          # head = last non-(C,S) segment
        else:
            # degenerate: every segment is C/S (e.g. HC 'ki' = [C]);
            # the last segment stands as head so it can be labeled
            hi = len(lst) - 1
        _s, p, t, tn = lst[hi]
        if p == "T" and t == "d":
            # trailing definite article: in Aramaic the article is a SUFFIX
            # (emphatic state, e.g. mlk' [N,Td]); step back to the lexical
            # segment. A leading T/d (Hebrew prefix article) is unaffected
            # because hi already points past it.
            earlier = [i for i in core_idx
                       if i < hi and not (lst[i][1] == "T"
                                          and lst[i][2] == "d")]
            if earlier:
                hi = earlier[-1]
                _s, p, t, tn = lst[hi]
        head = (p, t, tn)
        prefixes = lst[:hi]
        heads[pid] = {
            "head_pos": head[0] if head else None,
            "head_type": head[1] if head else None,
            "head_type_name": head[2] if head else None,
            "has_r_prefix": any(p == "R" for _, p, _, _ in prefixes),
            "et_prefix": any(p == "T" and t == "o"
                             for _, p, t, _ in prefixes),
            "has_suffix": any(p == "S" for _, p, _, _ in lst),
            "n_seg": len(lst),
        }
    return heads


def coarse_category(head_pos):
    return {"V": "verb", "N": "noun", "A": "adjective", "D": "adverb",
            "P": "pronoun", "T": "particle"}.get(head_pos, "unknown")


# ----------------------------------------------------------------------------
# role assignment (per verse)
# ----------------------------------------------------------------------------
def assign_roles(words, heads):
    """words: list of dicts in word_pos order. Returns list of (role, basis).

    Head = last morph segment that is not C (conjunction) or S (suffix);
    a trailing T/d steps back (Aramaic emphatic-state article suffix);
    standalone R is a preposition, standalone T a particle (documented in
    alignment_method.md).
    Rules:
      * et-marker token: strongs='H853' (Hebrew) with no lexical head, or a
        bare T/o head (morph T/o agrees 100% with H853 on these).
      * object: (a) self-marked -- T/o prefix bound to a noun/pronoun
        head (morph), or bound et- in the surface text (unpointed 'et-...',
        OSHB does not split these); (b) span-marked -- noun/pronoun head, no
        preposition prefix, inside the span after an et-marker up to the next
        verb, next marker, or verse end. [GKC section 117]
        Aramaic l- (coded T/o) is treated as a preposition prefix, never as
        the Hebrew marker (dative/accusative ambiguity, documented).
      * verbs: head V (incl. participles/infinitives -- documented heuristic).
      * personal pronouns (P/type p), no preposition prefix: subject.
      * other nouns, no preposition prefix: subject, basis unmarked-substantive
        (Hebrew subjects are unmarked nominatives).
      * noun/pronoun with preposition prefix: other/prepositional-phrase;
        bare R head: other/preposition.
      * non-personal pronouns: other/pronoun:<type>.
      * A -> qualifier:adj, D -> qualifier:adv.
      * particles -> other/particle:<type>; no morphology -> unresolved.
    """
    info = []
    for w in words:
        h = heads.get(w["morph_pattern_id"])
        if h is None:
            # pattern row exists but has no segments (unparsed), or no pattern
            info.append({"cat": "unknown", "head_pos": None, "head_type": None,
                         "head_type_name": None, "has_r_prefix": False,
                         "et_prefix": False, "degenerate": False,
                         "pure_marker": bool(w["strongs"] == "H853"
                                             and not w["is_aramaic"]),
                         "pronominal_marker": False,
                         "bound_et": False})
        else:
            cat = coarse_category(h["head_pos"])
            pure = (h["head_pos"] is None or
                    (h["head_pos"] == "T" and h["head_type"] == "o"))
            is_h853 = w["strongs"] == "H853" and not w["is_aramaic"]
            info.append({"cat": cat, "head_pos": h["head_pos"],
                         "head_type": h["head_type"],
                         "head_type_name": h["head_type_name"],
                         "has_r_prefix": h["has_r_prefix"],
                         "et_prefix": h["et_prefix"],
                         "degenerate": False,
                         "pure_marker": pure and is_h853
                         and not h["has_suffix"],
                         "pronominal_marker": pure and is_h853
                         and h["has_suffix"],
                         # bound marker: OSHB does not split the maqqef-bound
                         # marker (e.g. et-binkha HNcmsc/Sp2ms); the surface
                         # text carries it: unpointed 'et-...'
                         "bound_et": bool(not w["is_aramaic"]
                                          and (w["unpointed"] or "")
                                          .startswith("את-"))})

    # object spans: for each pure marker, following words until next verb,
    # next marker, or verse end
    in_span = [False] * len(words)
    for i, inf in enumerate(info):
        if not inf["pure_marker"]:
            continue
        for j in range(i + 1, len(words)):
            if info[j]["pure_marker"] or info[j]["cat"] == "verb":
                break
            in_span[j] = True

    out = []
    for w, inf, span in zip(words, info, in_span):
        aramaic = bool(w["is_aramaic"])
        dia = "|aramaic" if aramaic else ""
        cat = inf["cat"]
        # Aramaic l- (coded T/o) is ambiguous dative/accusative; without a
        # parser it is conservatively a preposition prefix, never the Hebrew
        # object marker.
        et_pref = inf["et_prefix"] and not aramaic
        prep_pref = inf["has_r_prefix"] or (inf["et_prefix"] and aramaic)
        self_marked = et_pref or inf["bound_et"]
        if inf["pure_marker"]:
            out.append(("other", "et-marker-token" + dia))
        elif inf["pronominal_marker"]:
            # marker + pronominal suffix: the suffix IS the object (e.g. oto)
            out.append(("object", "et-marker-pronominal" + dia))
        elif cat == "verb":
            out.append(("verb", "morph-verb" + dia))
        elif self_marked and cat in ("noun", "pronoun"):
            # self-marked: T/o prefix (morph) or bound et- (surface text)
            out.append(("object", "et-marker" + dia))
        elif span and cat in ("noun", "pronoun") and not prep_pref:
            out.append(("object", "et-marker" + dia))
        elif cat == "pronoun" and inf["head_type"] == "p" \
                and not prep_pref:
            out.append(("subject", "personal-pronoun" + dia))
        elif cat == "noun" and not prep_pref:
            out.append(("subject", "unmarked-substantive" + dia))
        elif cat in ("noun", "pronoun") and prep_pref:
            out.append(("other", "prepositional-phrase" + dia))
        elif cat == "adjective":
            out.append(("qualifier:adj", "morph-adjective" + dia))
        elif cat == "adverb":
            out.append(("qualifier:adv", "morph-adverb" + dia))
        elif cat == "pronoun":
            out.append(("other", "pronoun:%s" % (inf["head_type"] or "?") + dia))
        elif cat == "particle":
            tname = inf["head_type_name"] or "unknown"
            out.append(("other", "particle:%s" % tname + dia))
        elif inf["head_pos"] == "R":
            out.append(("other", "preposition" + dia))
        elif inf["head_pos"] == "C":
            out.append(("other", "conjunction" + dia))
        elif inf.get("degenerate"):
            out.append(("unresolved", "no-content-segment" + dia))
        else:
            basis = ("no-morphology" if w["morph_pattern_id"] is None
                     else "morph-unparsed")
            out.append(("unresolved", basis + dia))
    return out


# ----------------------------------------------------------------------------
# main build
# ----------------------------------------------------------------------------
def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys=ON")
    heads = load_pattern_heads(con)

    # ---- bulk loads ---------------------------------------------------------
    words_by_verse = {}
    word_verse = {}
    for wid, vid, wpos, pointed, unpointed, strongs, aram, mpid in con.execute(
            "SELECT word_id, verse_id, word_pos, pointed, unpointed, strongs,"
            " is_aramaic, morph_pattern_id FROM words"
            " ORDER BY verse_id, word_pos"):
        d = {"word_id": wid, "verse_id": vid, "word_pos": wpos,
             "pointed": pointed, "unpointed": unpointed,
             "strongs": strongs, "is_aramaic": aram,
             "morph_pattern_id": mpid}
        words_by_verse.setdefault(vid, []).append(d)
        word_verse[wid] = vid

    kjv_by_verse = {}
    for kid, vid, kpos, kw in con.execute(
            "SELECT kjv_word_id, verse_id, kjv_pos, kjv_word FROM kjv_words "
            "ORDER BY verse_id, kjv_pos"):
        kjv_by_verse.setdefault(vid, []).append((kid, kpos, kw))

    render_texts = {}   # word_id -> [kjv_word texts in rendering_id order]
    for wid, kw in con.execute(
            "SELECT word_id, kjv_word FROM kjv_renderings "
            "ORDER BY word_id, rendering_id"):
        render_texts.setdefault(wid, []).append(kw)

    ylt_by_word = {}    # word_id -> [(rendering_id, ylt_word, ylt_word_pos)]
    for rid, wid, yw, ypos in con.execute(
            "SELECT rendering_id, word_id, ylt_word, ylt_word_pos "
            "FROM ylt_renderings ORDER BY word_id, ylt_word_pos"):
        ylt_by_word.setdefault(wid, []).append((rid, yw, ypos))

    stats = {k: 0 for k in (
        "base_rows", "kjv_satellites", "ylt_satellites",
        "words_no_kjv_rendering", "words_no_ylt_rendering",
        "dup_text_hits", "dangling_renderings", "kjv_took_later_candidate",
        "kjv_null_despite_renderings", "translator_supplied_kjv",
        "extra_kjv_rendering", "extra_ylt_rendering")}

    rows = []  # (verse_id, region, tiebreak, hebrew_word_id, kjv_word_id,
               #  ylt_rendering_id, role, basis)

    for vid in sorted(set(words_by_verse) | set(kjv_by_verse)):
        ws = words_by_verse.get(vid, [])
        roles = assign_roles(ws, heads)

        # ---- KJV claiming ------------------------------------------------
        krows = kjv_by_verse.get(vid, [])
        text_to_ids = {}
        for kid, kpos, kw in krows:
            text_to_ids.setdefault(kw, []).append((kpos, kid))
        rtexts = set()
        for w in ws:
            rtexts.update(render_texts.get(w["word_id"], ()))
        claimed = set()
        word_kjv = {}
        for w in ws:
            wid = w["word_id"]
            texts = render_texts.get(wid)
            if not texts:
                stats["words_no_kjv_rendering"] += 1
                word_kjv[wid] = None
                continue
            cands = []
            for t in texts:
                ids = text_to_ids.get(t, ())
                if len(ids) > 1:
                    stats["dup_text_hits"] += 1
                if not ids:
                    stats["dangling_renderings"] += 1
                cands.extend(kid for _, kid in ids)
            seen, dedup = set(), []
            for kid in cands:
                if kid not in seen:
                    seen.add(kid)
                    dedup.append(kid)
            pick, first = None, True
            for kid in dedup:
                if kid not in claimed:
                    pick = kid
                    if not first:
                        stats["kjv_took_later_candidate"] += 1
                    break
                first = False
            if pick is None:
                stats["kjv_null_despite_renderings"] += 1
            else:
                claimed.add(pick)
            word_kjv[wid] = pick

        # ---- YLT primary ---------------------------------------------------
        word_ylt = {}
        ylt_extra = []
        for w in ws:
            rl = ylt_by_word.get(w["word_id"])
            if not rl:
                stats["words_no_ylt_rendering"] += 1
                word_ylt[w["word_id"]] = None
                continue
            word_ylt[w["word_id"]] = rl[0][0]
            for rid, yw, ypos in rl[1:]:
                ylt_extra.append((ypos, rid, w["word_id"]))
                stats["extra_ylt_rendering"] += 1

        # ---- base rows ------------------------------------------------------
        for w, (role, basis) in zip(ws, roles):
            rows.append((vid, REGION[role], w["word_pos"], w["word_id"],
                         word_kjv[w["word_id"]], word_ylt[w["word_id"]],
                         role, basis))
            stats["base_rows"] += 1

        # ---- KJV satellites --------------------------------------------------
        for kid, kpos, kw in krows:
            if kid in claimed:
                continue
            if kw in rtexts:
                role, basis = "other", "extra-kjv-rendering"
                stats["extra_kjv_rendering"] += 1
            else:
                role, basis = "translator-supplied", "no-rendering-reference"
                stats["translator_supplied_kjv"] += 1
            rows.append((vid, REGION["translator-supplied"], kpos, None, kid,
                         None, role, basis))
            stats["kjv_satellites"] += 1

        # ---- YLT satellites ---------------------------------------------------
        for ypos, rid, wid in sorted(ylt_extra):
            rows.append((vid, REGION["translator-supplied"], 10_000_000 + ypos,
                         None, None, rid, "other",
                         f"extra-ylt-rendering:{wid}"))
            stats["ylt_satellites"] += 1

    # ---- write (idempotent) ---------------------------------------------------
    con.execute("DROP TABLE IF EXISTS word_alignment")
    con.execute("""CREATE TABLE word_alignment(
      alignment_id   INTEGER PRIMARY KEY,
      verse_id       INTEGER NOT NULL REFERENCES verses(verse_id),
      seq            INTEGER NOT NULL,
      hebrew_word_id INTEGER REFERENCES words(word_id),
      kjv_word_id    INTEGER REFERENCES kjv_words(kjv_word_id),
      ylt_rendering_id INTEGER REFERENCES ylt_renderings(rendering_id),
      syntactic_role TEXT NOT NULL,
      role_basis     TEXT NOT NULL,
      UNIQUE(verse_id, seq)
    )""")
    con.execute("CREATE INDEX idx_alignment_hebrew ON word_alignment(hebrew_word_id)")
    con.execute("CREATE INDEX idx_alignment_verse ON word_alignment(verse_id, seq)")

    # seq dense per verse: order rows by (verse_id, region, tiebreak)
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out, last_vid, seq = [], None, 0
    for (vid, _region, _tie, hid, kid, yid, role, basis) in rows:
        if vid != last_vid:
            last_vid, seq = vid, 0
        seq += 1
        out.append((vid, seq, hid, kid, yid, role, basis))
    con.executemany(
        "INSERT INTO word_alignment(verse_id, seq, hebrew_word_id, kjv_word_id,"
        " ylt_rendering_id, syntactic_role, role_basis)"
        " VALUES (?,?,?,?,?,?,?)", out)
    con.commit()

    # ---- verification ---------------------------------------------------------
    print("== build stats ==")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  total rows: {len(out)}")

    checks = []
    def check(name, sql, expect):
        got = con.execute(sql).fetchone()[0]
        ok = got == expect
        checks.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: got {got}, expect {expect}")

    check("words rows each exactly once as hebrew_word_id",
          "SELECT COUNT(*) FROM (SELECT hebrew_word_id FROM word_alignment "
          "WHERE hebrew_word_id IS NOT NULL GROUP BY 1 HAVING COUNT(*)=1)",
          con.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    check("base rows == words count",
          "SELECT COUNT(*) FROM word_alignment WHERE hebrew_word_id IS NOT NULL",
          con.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    check("every kjv_words row referenced exactly once",
          "SELECT COUNT(*) FROM (SELECT kjv_word_id FROM word_alignment "
          "WHERE kjv_word_id IS NOT NULL GROUP BY 1 HAVING COUNT(*)=1)",
          con.execute("SELECT COUNT(*) FROM kjv_words").fetchone()[0])
    check("every ylt_renderings row referenced exactly once",
          "SELECT COUNT(*) FROM (SELECT ylt_rendering_id FROM word_alignment "
          "WHERE ylt_rendering_id IS NOT NULL GROUP BY 1 HAVING COUNT(*)=1)",
          con.execute("SELECT COUNT(*) FROM ylt_renderings").fetchone()[0])
    check("seq dense 1..N per verse (no gaps, min=1)",
          "SELECT COUNT(*) FROM (SELECT verse_id FROM word_alignment "
          "GROUP BY verse_id HAVING COUNT(*) != MAX(seq) OR MIN(seq) != 1)",
          0)
    check("PRAGMA foreign_key_check clean",
          "SELECT COUNT(*) FROM pragma_foreign_key_check('word_alignment')", 0)

    print("== role distribution ==")
    for role, n in con.execute(
            "SELECT syntactic_role, COUNT(*) FROM word_alignment "
            "GROUP BY 1 ORDER BY 2 DESC"):
        print(f"  {role}: {n}")

    # ---- hand-check verses ------------------------------------------------------
    print("== hand-check verses ==")
    for vid, label in [(1, "Gen 1:1 narrative+et"), (14339, "Ps 23:1 poetry"),
                       (2059, "Ex 20:2 law"), (21930, "Dan 2:4 aramaic"),
                       (550, "Gen 22:2 et-chain"), (17813, "Isa 1:1 prophecy"),
                       (16616, "Prov 3:5 wisdom"), (5121, "Deut 6:4 verbless"),
                       (89, "Gen 4:9 interrogative"),
                       (929, "Gen 31:55 orphan-verse")]:
        ref = con.execute(
            "SELECT b.name_en || ' ' || v.chapter || ':' || v.verse "
            "FROM verses v JOIN books b ON b.book_id=v.book_id "
            "WHERE v.verse_id=?", (vid,)).fetchone()
        print(f"--- {label} ({ref[0] if ref else '?'}) ---")
        for seqn, role, basis, pointed, kw, yw in con.execute(
                "SELECT a.seq, a.syntactic_role, a.role_basis, w.pointed,"
                " k.kjv_word, y.ylt_word FROM word_alignment a"
                " LEFT JOIN words w ON w.word_id=a.hebrew_word_id"
                " LEFT JOIN kjv_words k ON k.kjv_word_id=a.kjv_word_id"
                " LEFT JOIN ylt_renderings y ON y.rendering_id=a.ylt_rendering_id"
                " WHERE a.verse_id=? ORDER BY a.seq", (vid,)):
            print(f"  {seqn:3d} {role:18s} {str(pointed):14s} "
                  f"KJV={kw} YLT={yw} [{basis}]")

    if not all(checks):
        sys.exit("VERIFICATION FAILED")
    print("ALL VERIFICATIONS PASSED")


if __name__ == "__main__":
    main()
