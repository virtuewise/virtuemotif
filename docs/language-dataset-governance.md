# Multilingual language dataset governance

The language-ID benchmark must distinguish a synthetic regression fixture from
a real evaluation dataset. The validator in `tools/validate_language_dataset.py`
checks the versioned JSON structure and requires provenance/governance fields
before a corpus can declare itself native-speaker-reviewed and rights-cleared.

## Validate the repository smoke fixture

From the repository root:

```bash
python -m tools.validate_language_dataset
python -m pytest -q tests/test_validate_language_dataset.py
```

The starter fixture is intentionally marked
`synthetic_smoke_only_requires_native_speaker_review`. Every example must use
the `smoke` split. Passing validation only means the fixture conforms to its
declared structural contract; it is not a measure of language-ID quality.

## Reviewed corpus contract

A future corpus may use status `native_speaker_reviewed_rights_cleared` only
after the dataset owner has actually established the required facts. It must
include:

- Top-level governance fields `rights_status: rights_cleared`,
  `consent_status: documented`, and
  `review_status: native_speaker_reviewed`.
- A documented adjudication policy and a split policy that separates sources,
  songs, and speakers between training/development and held-out test data.
- Unique example IDs, non-empty text, a language label present in the corpus
  label list, and explicit `train` or `test` membership.
- Per-example pseudonymous `source_id` and `speaker_id`, `reviewer_ids`,
  `review_status: native_speaker_reviewed`, and a `consent_ref` that points
  to an access-controlled record outside the public repository.

The validator checks that a source or speaker identifier does not occur across
multiple dataset splits. It cannot verify that distinct pseudonyms refer to
distinct real sources or people, so split design must be stewarded and audited.

Use pseudonymous identifiers, not real names or contact details. Keep raw consent
documents, personal data, private contributor communications, and any
restricted source material outside GitHub. Only add examples whose rights and
permitted evaluation use are clear.

## Benchmark interpretation: confidence and code-switching

The language-ID report includes binary code-switch metrics for the reference
mul label (precision, recall, F1, support, and confusion counts) and a
10-bin top-label confidence diagnostic. The latter reports expected calibration
error (ECE), a Brier score against whether each top prediction is correct, and
per-bin mean confidence versus observed accuracy.

These are diagnostic calculations, not a claim that the lexical detector's
heuristic confidence is a calibrated probability. Empty bins are omitted. The
metrics are only as representative as the reviewed corpus and must not be
interpreted as real-world estimates when the dataset status is synthetic smoke.
Code-switch precision/recall also depend on the annotation policy for mixed,
short, ambiguous, and boundary-spanning examples.

The validator cannot independently confirm consent, licensing, fluency, or that
a review occurred. Required metadata can still be falsely asserted, so human
stewardship and auditable records remain necessary. Never relabel the current
synthetic fixture as reviewed to make a benchmark pass. Public CI should continue
using synthetic smoke data; private or licensed evaluation data should be stored
and tested according to its access restrictions.
