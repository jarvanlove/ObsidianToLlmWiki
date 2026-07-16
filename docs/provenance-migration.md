# Provenance Migration

Legacy knowledge pages may contain source links in body text or relation fields without structured frontmatter.

Audit first:

```powershell
python .\00_system\scripts\migrate_provenance.py --format json
```

Apply only evidence already present in the page:

```powershell
python .\00_system\scripts\migrate_provenance.py --apply --path <wiki-relative-page>
```

The migration may recover `source_notes`, explicit `p.N`/`pp.N-M` references, `provenance_status`, and `provenance_checked`. A document-length phrase such as “114 pages” is not treated as a page citation. Missing page references remain `partial` and must be completed by checking the original document or its section notes.
