Living document — update these diagrams when adding features.

# bible-project — Architecture

**Relationship to Bible:** this repo is the current, live Bible Project. `cosbykit-afk/Bible` is an earlier partial copy of the same project — its own repo description says so ("Earlier partial Bible-database copy; current work continues in the bible-project repository"). Do not treat them as two independent systems: bible-project is the continuation with the U-8 maqqef-component repair, the U-9 verse-remap repair, YLT word alignment, and the Flask translation website, none of which exist in the older Bible repo.

## 1. Context diagram (level 0)

```mermaid
flowchart LR
    E1["Kit developer"]
    E2["Kit reader"]
    E3["Spreadsheet files"]
    E4["OSHB Hebrew text"]
    E5["KJV word data"]
    E6["YLT verse data"]
    E7["BDB lexicon data"]
    P0("Bible Project system")
    E1 -->|"runs build scripts"| P0
    E2 -->|"browses and picks translations"| P0
    E3 -->|"Hebrew text plus Strongs plus morphology"| P0
    E4 -->|"KJV words with Strongs tags"| P0
    E5 -->|"verse level translation"| P0
    E6 -->|"dictionary glosses"| P0
    E7 -->|"verse level translation USFM"| P0
    P0 -->|"built corpus and reports"| E1
    P0 -->|"verse reader with word dropdowns"| E2
```

## 2. Level-1 data flow diagram

```mermaid
flowchart LR
    E1["Kit developer"]
    E2["Kit reader"]
    E3["Source text providers"]
    P1("1.0 Ingest canonical word list")
    P2("2.0 Crosswalk words to OSHB")
    P3("3.0 Load renderings and glosses")
    P4("4.0 Build roots and lexicon")
    P5("5.0 Align YLT and run repairs")
    P6("6.0 Assemble SQLite corpus")
    P7("7.0 Serve translation website")
    D1[("D1 staged input files")]
    D2[("D2 bible db read only corpus")]
    D3[("D3 app db user data")]
    D4[("D4 choice byte files")]
    E1 -->|"runs scripts"| P1
    E3 -->|"spreadsheets OSHB KJV YLT lexicons"| P1
    P1 -->|"canonical words"| D1
    D1 -->|"canonical words"| P2
    D1 -->|"parsed source data"| P3
    P2 -->|"aligned words"| P6
    P3 -->|"renderings glosses verses"| P6
    D1 -->|"base words"| P4
    P4 -->|"root tiers lexicon"| P6
    D1 -->|"KJV and YLT tokens"| P5
    P5 -->|"word alignments repairs"| P6
    P6 -->|"assembled corpus"| D2
    P6 -->|"reports"| E1
    E2 -->|"HTTP requests"| P7
    P7 -->|"reads corpus"| D2
    P7 -->|"reads and writes"| D3
    P7 -->|"reads and writes bytes"| D4
    P7 -->|"reader pages"| E2
```

## 3. Entity–relationship diagram

```mermaid
erDiagram
    BOOK {
        int book_id PK
        string english_name
        string hebrew_name
    }
    WORD {
        int word_id PK
        int book_id FK
        string text
        string root_code
        string strongs
    }
    KJV_WORD {
        int kjv_word_id PK
        string english_text
        string strongs
    }
    KJV_RENDERING {
        int rendering_id PK
        int word_id FK
        string english_text
        string method
    }
    YLT_VERSE {
        int verse_id PK
        string text
    }
    YLT_RENDERING {
        int rendering_id PK
        int word_id FK
        string ylt_word
    }
    GLOSS {
        string strongs PK
        string gloss_text
    }
    ROOT_ENTRY {
        int root_id PK
        string base_word
    }
    ROOT_FORM {
        int form_id PK
        int root_id FK
        string affix_pattern
    }
    ROOT_VOWEL {
        int vowel_id PK
        int root_id FK
        int form_id FK
        string pointed_form
    }
    LEXICON {
        int lexicon_id PK
        string kjv_renderings
        string ylt_renderings_computed
        string verse_list
    }
    APP_USER {
        int user_id PK
        string name
        string created_at
    }
    TRANSLATION {
        int translation_id PK
        int user_id FK
        string name
        string description
        string created_at
        string updated_at
    }
    OTHER_OPTION {
        int option_id PK
        int translation_id FK
        int idx
        string text
        string created_at
    }
    CHOICES_FILE {
        string path PK
        int size_bytes
        int byte_offset
    }
    BOOK ||--o{ WORD : contains
    ROOT_ENTRY ||--o{ ROOT_FORM : has
    ROOT_FORM ||--o{ ROOT_VOWEL : has
    ROOT_VOWEL ||--|| LEXICON : describes
    WORD ||--o{ KJV_RENDERING : rendered_as
    WORD ||--o{ YLT_RENDERING : rendered_as
    WORD }o--|| GLOSS : glossed_by
    APP_USER ||--o{ TRANSLATION : owns
    TRANSLATION ||--o{ OTHER_OPTION : adds
    TRANSLATION ||--|| CHOICES_FILE : stores_choices_in
```

## Grounding notes

- Observed: README.md documents the same 11-table corpus as the older repo plus `ylt_renderings` (337,601 rows, computed best-effort); exact row counts for words 264,217, kjv_renderings 631,950, kjv_words 610,324, ylt_verses 23,145, glosses 17,347, books 39, root_entry 30,087, root_form 57,724, root_vowel 126,869, lexicon 126,869.
- Observed: repair scripts named `repair_u8_maqqef_kjv.py`, `repair_u8_lexicon.py`, `repair_u9_verse_remap_kjv.py`, `repair_u9_lexicon.py`, `u9_verse_remap.tsv`, plus `build_ylt_align.py` and `measure_ylt_coverage.py` — the basis for process 5.0. README describes the U-8 maqqef-component repair and U-9 verse-remap repair with before/after coverage figures.
- Observed: `worker-out/` subdirectories (canon, kjv, lexicons, oshb, ylt) with staged TSV/zip/USFM inputs and per-source README.txt — the basis for D1.
- Observed: `website/app.py` (Flask, port 5057): opens bible.db read-only, app.db read-write, `user_data/translation_<id>.choices` byte files; routes for book/chapter/verse/word/choice/translations/reading/export. `website/schema.sql` defines `app_user`, `translation`, `other_option` verbatim. `website/STATUS.md` documents the end-to-end local test (all routes 200, choice persistence, reading composition, export).
- Observed: the repo ships its own `website_er.mmd` / `website_system.mmd` Mermaid sources — the website half of this ERD and DFD follows their structure (entities, byte-file choice storage, cross-database logical FK on word_id).
- INFERRED: process numbering 1.0–6.0 groups scripts by README-described purpose (ingest → crosswalk → renderings → roots/lexicon → alignment/repairs → assemble); the repo documents each script's role but no explicit pipeline wiring between them, so the numbered process boundaries are inferred.
- INFERRED: ERD primary/foreign key names and attributes for the corpus tables (words, kjv_renderings, ylt_renderings, glosses, root_*, lexicon) are inferred from README prose; no corpus schema.sql was observed. Website entity attributes were observed verbatim in schema.sql.
- INFERRED: that the flat choices file (one byte per word at offset word_id−1) and cross-db word_id references are enforced by application code only — observed in schema.sql comments and STATUS.md, stated as design fact by the repo.
