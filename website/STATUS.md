# Bible website — status

SDLC workflow: `bible-website` (saved workflow `~/.jarvis/workflows/bible-website.js`).
Spec (Kit, 2026-09-22): drop-down over each Hebrew word — KJV rendering, Young's rendering,
Other (user-defined, the academic pass). Browse book → chapter → verse → words.
Choosing word by word builds and saves his translation.

Corpus `bible.db` stays READ-ONLY. Website storage:
- `app.db`: `app_user`, `translation`, `other_option` (multi-value "Other" renderings).
- `user_data/translation_<id>.choices`: ONE BYTE PER WORD (264,217 bytes),
  byte at offset (word_id − 1). Byte = drop-down item number selected:
  0 = default (no choice); rest index into the word's drop-down list rebuilt
  identically as [KJV renderings | Young's-computed renderings | Other options].

## Log

- 2026-09-22 ~03:30 PT: project ordered ("let's build it"); SDLC invoked.
  Design phase: website ER diagram + system diagram drawn
  (`website/website_er.png`, `website/website_system.png`; builder `website_diagrams.py`).
- 2026-09-22 ~03:27 PT: YLT word alignment in progress (`build_ylt_align.py`):
  verse-by-verse, YLT tokens ↔ KJV tokens (monolingual Needleman-Wunsch),
  KJV → Hebrew via shared Strong's. Output `ylt_renderings(word_id, ylt_word, ylt_word_pos)`.
  COMPUTED best-effort, not a source alignment.
- Implementation / test / verify phases: not started.
- 2026-09-22 ~03:40 PT: YLT alignment COMPLETE (exit 0, 232s): 23,006 verses,
  598,514 YLT tokens, 215,533 mapped to Hebrew (36.0%); 262,062 Hebrew words,
  114,269 with >=1 YLT word (43.6%); 259,171 ylt_renderings rows.
  Coverage honest-measured (measure_ylt_coverage.py): per-book Hebrew-word hit
  26.8% (Joel) to 52.9% (Ezra); 56.8% of Hebrew words have no YLT rendering,
  59.2% of those unbridgeable (blank Strong's). 65.1% of hit words map to >1
  distinct YLT word. Spot-checks (Ex 20:2, Ps 23:1, Isa 53:5, Obad 1:1) show
  real errors (e.g. H3068 -> "from", H2637 -> "not"). COMPUTED, not authoritative.
- 2026-09-22 ~03:45 PT: lexicon.ylt_renderings_computed added
  (build_lexicon_ylt.py): 62,323/126,869 rows (49.1%), frequency-ordered,
  ' | '-separated, labeled computed.
- 2026-09-22 ~03:50 PT: website/schema.sql created (app_user, translation,
  translation_choice with chosen_source IN ('kjv','ylt','other'),
  UNIQUE(translation_id, word_id)).
- 2026-09-22 ~03:55 PT: Flask app built (website/app.py, port 5057): routes /,
  /book/<n>, /chapter/<n>/<c>, /verse/<n>/<c>/<v> (per-word KJV/Young's-computed/
  Other dropdown + save), POST /choice, /translations (create/select),
  /reading/<tid>/<n>/<c>/<v>, /export/<tid>, /word/<wid> (pointed/unpointed,
  letters, root code, Strong's, renderings, contexts, verses).
- 2026-09-22 ~04:00 PT: tested locally end-to-end: all routes 200; created
  translation, saved KJV + Other choices, verified persistence (2 checks),
  reading view composes, export downloads, word detail renders. Test data
  removed (app.db deleted; recreated on first run).
- 2026-09-22 ~03:45 PT (Kit's directive: "a byte per word"): choice storage
  redesigned from SQL rows to a flat index file — `user_data/translation_<id>.choices`,
  264,217 bytes, byte at offset (word_id − 1) = selected drop-down item number
  (0 = default; rest index into [KJV | Young's-computed | Other options]).
  `translation_choice` table replaced by `other_option` (multi-value Other
  renderings). ER + system diagrams redrawn (`website_diagrams.py`) showing the
  byte file. Retested end-to-end: byte file correct on disk, other_option row
  saved, verse/reading/export all resolve bytes correctly. Test data removed.
