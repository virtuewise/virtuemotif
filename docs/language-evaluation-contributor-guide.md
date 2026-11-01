# Multilingual lyric evaluation: contributor starter kit

This workflow helps contributors collect **new, permissioned examples** for evaluation without committing lyrics or personal information prematurely. It does not itself recruit reviewers, collect consent, or certify rights.

## 1. Eligible examples

Prefer short text authored by a consenting fluent speaker, or text whose license explicitly permits the intended evaluation and storage. Do not paste commercial lyrics, scraped lyric websites, private messages, or identifiable personal information into an issue or pull request. Do not treat a public URL as proof that redistribution is permitted.

Target labels include:
- `sn`: Shona
- `nd`: isiNdebele
- `zu`: isiZulu
- `en`: English
- `mul`: naturally code-switched text, under a documented annotation policy
- `und`: insufficient evidence, unknown, or out-of-scope language

Add further languages only with an explicit label definition and review plan. Do not infer language from ethnicity, location, or a person's name.

## 2. Suggested annotation flow

1. A contributor drafts a short example and records its source/provenance privately.
2. A data steward confirms permitted use and storage before the text enters the evaluation repository.
3. Two fluent reviewers independently label the text, its language variety when known and voluntarily supplied, and any code-switch spans.
4. Reviewers record uncertainty rather than forcing a language label for overlapping vocabulary or very short text.
5. A steward adjudicates disagreements and records the decision without publishing personal information.
6. Split by source/song and speaker before tuning; keep held-out test examples out of marker/threshold development.
7. Run the schema validator and benchmark, then publish a report with dataset version, split, counts, limitations, and per-language metrics. Before calling a dataset release-ready, run the fail-closed release gate below.

## 3. Minimum metadata

Keep the following metadata for each approved example in the access-controlled annotation ledger:
- stable pseudonymous example, source, and speaker identifiers
- text and reference label, with mixed-language spans if applicable
- source type and rights/license reference or external consent-record reference
- permitted uses and storage/retention restrictions
- reviewer identifiers as pseudonyms, expertise/variety information volunteered by reviewers, review date, independent labels, adjudication status, and uncertainty notes
- assigned split and the reason for any exclusion

Keep raw consent records and contact details outside GitHub. Never publish private reviewer identity or raw consent documents. Only publish an example when both rights and the publication/storage permission are explicit.

## 4. Dataset release checklist

- [ ] Rights holder or contributor permission covers the exact intended storage and evaluation use.
- [ ] No identifying personal data or restricted material is included.
- [ ] At least two fluent reviewers independently annotated the example.
- [ ] Disagreements, ambiguity, and code-switch boundaries are adjudicated or explicitly marked unresolved.
- [ ] Source and speaker grouping is checked before split assignment.
- [ ] Held-out test material is not used for tuning.
- [ ] Dataset status and report accurately describe review coverage and remaining limitations.

A filled checklist or metadata field is not independent proof that the underlying claim is true. A named data steward remains accountable for auditing records. If permission or label confidence is unclear, exclude the example or keep it private pending review.

## 5. Run the release gate

From the repository root, validate the schema and then run the release gate against the candidate corpus:

```bash
python -m tools.validate_language_dataset path/to/candidate.json
python -m tools.language_release_gate path/to/candidate.json
python -m tools.benchmark_language_id --corpus path/to/candidate.json --output language-report.json
```

The release gate blocks the synthetic smoke fixture and any corpus that fails the reviewed-dataset schema, required metadata, or source/speaker split checks. A successful result means **structurally valid according to declared metadata only**. It does not prove that rights, consent, reviewer qualifications, annotations, or representativeness are genuine; the data steward must independently audit the private provenance ledger. Never place raw consent records or contact details in the repository.
