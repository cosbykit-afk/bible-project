#!/usr/bin/env python3
"""Decode the CrossWire SWORD KJV module (zText format) OT into raw verse texts.

zText layout (from jsword ZVerseBackend javadoc + code):
  ot.bzv : per-verse 10-byte LE records: blockNum u32, verseStart u32, verseSize u16
  ot.bzs : per-block 12-byte LE records: blockStart u32, blockSize u32, uncompressedSize u32
  ot.bzz : concatenated zlib-compressed blocks
Verse index = testament ordinal in the module's KJV versification (empty slots
have verseSize == 0 and are skipped).

Output: /tmp/kjv_ztext_verses.json -> list of dicts {idx, osis, text}
  osis = osisID from the <verse> marker (e.g. "Gen.1.1"); text = raw OSIS XML
  of the verse entry.
"""
import json
import struct
import zipfile
import zlib

ZIP_PATH = "/tmp/kjv.zip"

BOOK_ABBR = {'Gen': 1, 'Exod': 2, 'Lev': 3, 'Num': 4, 'Deut': 5, 'Josh': 6,
             'Judg': 7, 'Ruth': 8, '1Sam': 9, '2Sam': 10, '1Kgs': 11,
             '2Kgs': 12, '1Chr': 13, '2Chr': 14, 'Ezra': 15, 'Neh': 16,
             'Esth': 17, 'Job': 18, 'Ps': 19, 'Prov': 20, 'Eccl': 21,
             'Song': 22, 'Isa': 23, 'Jer': 24, 'Lam': 25, 'Ezek': 26,
             'Dan': 27, 'Hos': 28, 'Joel': 29, 'Amos': 30, 'Obad': 31,
             'Jonah': 32, 'Mic': 33, 'Nah': 34, 'Hab': 35, 'Zeph': 36,
             'Hag': 37, 'Zech': 38, 'Mal': 39}


def main():
    z = zipfile.ZipFile(ZIP_PATH)
    base = "modules/texts/ztext/kjv/ot"
    comp = z.read(base + ".bzv")
    idx = z.read(base + ".bzs")
    txt = z.read(base + ".bzz")

    n_verses = len(comp) // 10
    n_blocks = len(idx) // 12
    print(f"comp records: {n_verses}, blocks: {n_blocks}")
    assert len(comp) % 10 == 0 and len(idx) % 12 == 0

    blocks = []
    for b in range(n_blocks):
        blockStart, blockSize, uncompSize = struct.unpack_from("<III", idx, b * 12)
        raw = txt[blockStart:blockStart + blockSize]
        data = zlib.decompress(raw)
        assert len(data) == uncompSize, f"block {b}: {len(data)} != {uncompSize}"
        blocks.append(data)
    print(f"decompressed {n_blocks} blocks OK")

    import re
    verses = []
    empty = 0
    for i in range(n_verses):
        blockNum, verseStart, verseSize = struct.unpack_from("<IIH", comp, i * 10)
        if verseSize == 0:
            empty += 1
            continue
        entry = blocks[blockNum][verseStart:verseStart + verseSize].decode("utf-8", errors="replace")
        m = re.search(r'<verse[^>]*osisID="([^"]+)"', entry)
        osis = m.group(1) if m else None
        verses.append({"idx": i, "osis": osis, "text": entry})
    print(f"non-empty verses: {len(verses)}, empty slots: {empty}")

    # map osisID -> (book_num, chapter, verse)
    bad = [v for v in verses if not v["osis"]]
    print("verses without osisID:", len(bad))
    mapped = []
    unmapped_abbr = set()
    for v in verses:
        parts = v["osis"].split(".")
        abbr = parts[0]
        if abbr in BOOK_ABBR and len(parts) == 3:
            mapped.append({"book_num": BOOK_ABBR[abbr], "chapter": int(parts[1]),
                           "verse": int(parts[2]), "idx": v["idx"], "text": v["text"]})
        else:
            unmapped_abbr.add(v["osis"])
    print("mapped:", len(mapped), "unmapped osisIDs:", sorted(unmapped_abbr)[:10])
    if mapped:
        print("first:", mapped[0]["book_num"], mapped[0]["chapter"], mapped[0]["verse"])
        print("last:", mapped[-1]["book_num"], mapped[-1]["chapter"], mapped[-1]["verse"])
        print("sample entry text:", mapped[0]["text"][:400])

    json.dump(mapped, open("/tmp/kjv_ztext_verses.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
