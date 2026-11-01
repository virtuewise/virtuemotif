# Free dataset discovery and rights-aware ingestion

VirtueMotif now maintains a small, source-checked catalog of free multilingual
speech datasets. This is a **discovery and governance starting point**, not a
claim that these datasets contain songs or establish real-world singing
accuracy.

## Cataloged sources

| Dataset | Language | License reported by source | Reported size | Intended use here |
| --- | --- | --- | ---: | --- |
| [Common Voice Spontaneous Speech 5.0 — Shona](https://mozilladatacollective.com/datasets?q=Common+Voice+Spontaneous+Speech) | Shona (`sn`) | CC0-1.0 | 1.53 MB | Auxiliary speech/ASR language coverage |
| [Common Voice Spontaneous Speech 5.0 — English](https://mozilladatacollective.com/datasets?q=Common+Voice+Spontaneous+Speech) | English (`en`) | CC0-1.0 | 519.05 MB | Auxiliary speech/ASR baseline |
| [Common Voice Scripted Speech 27.0 — Zulu](https://mozilladatacollective.com/datasets/cmu610aue00jtnq07hnb00xio) | isiZulu (`zu`) | CC0-1.0 | 8.22 MB | Auxiliary speech/ASR coverage |
| [Common Voice Scripted Speech 27.0 — Xhosa](https://mozilladatacollective.com/datasets/cmu60x5rv00ilo1070jbpgna2) | isiXhosa (`xh`) | CC0-1.0 | 2.37 MB | Related-language research only; do not treat as isiNdebele |

The Shona and English links above are filtered catalog listings, not immutable
dataset archive URLs. Re-confirm the exact release and download terms on the
source before obtaining any files. Catalog entries record what the source
reported when reviewed; they are not legal advice or a substitute for checking
the current data-use terms.

The current source pages describe Common Voice releases as intended for ASR
training/evaluation and state that users must not attempt to identify speakers
or re-host/re-share dataset files. Respect those restrictions. Never commit
the audio, source archives, personal information, or raw corpus exports to this
repository. Keep data in a controlled local or private storage location and
record the exact version, source, checksum, acquisition date, and permitted
uses in the private provenance ledger.

## Important coverage gaps

- The catalog contains **speech**, not music or singing. It can help bootstrap
  language-aware transcription, but cannot replace a song-domain benchmark.
- The listed Shona release is small. The Zulu and Xhosa release records also
  report few validated clips. They are not representative enough to establish
  broad dialect or accent coverage.
- No isiNdebele (`nd`) source is currently marked approved in this catalog.
  Do not relabel isiZulu or isiXhosa data as isiNdebele.
- No mixed-language (`mul`) music dataset is approved yet.
- Real-world evaluation still requires rights-cleared song examples, independent
  fluent-speaker annotations, adjudication, and a source/speaker-disjoint test
  split.

## Validate and inspect the catalog

Run from the repository root:

```bash
python -m tools.free_dataset_catalog
python -m tools.free_dataset_catalog --language sn
python -m tools.free_dataset_catalog --language zu
python -m pytest tests/test_free_dataset_catalog.py
```

The validator fails closed on missing metadata, unknown licenses, non-HTTPS
source URLs, duplicate IDs, or missing restrictions/limitations. It does not
download data or certify that a source's claims are authentic. An operator must
verify current terms and approve any acquisition explicitly.

## Acquisition policy

1. Check the exact release's license, source-specific terms, intended-use
   statement, retention rules, and no-redistribution/no-identification clauses.
2. Do not ingest a dataset if training/model-development use is unclear.
3. Download only after explicit operator approval; keep audio out of Git.
4. Record source URL, version, retrieval date, checksum, language, task, and
   applicable restrictions.
5. Deduplicate by source/song and speaker before assigning train/validation/test.
6. Treat speech corpora as auxiliary training data only. Evaluate singing models
   on a separate rights-cleared, human-reviewed music test set.
