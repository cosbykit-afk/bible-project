# Bible database dump

`bible_dump.sql.gz` is split into 4 parts (`bible_dump.sql.gz.part-aa` …
`.part-ad`) because GitHub's API rejects single uploads of this size.

## Reassemble

```sh
cat bible_dump.sql.gz.part-* > bible_dump.sql.gz
```

## Restore

```sh
gunzip bible_dump.sql.gz
psql -U postgres -d bible -f bible_dump.sql
```

## Contents

- pg_dump of the `bible` PostgreSQL database from the Toetop laptop (WSL lampy distro)
- 23,145 YLT verses with 768-dim `nomic-embed-text` embeddings
- Dumped 2026-09-30; original size ~229 MB, gzipped ~85 MB
