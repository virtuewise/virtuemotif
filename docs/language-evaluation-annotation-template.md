# Annotation ledger template

Use this as an **access-controlled working template**, not as proof that any example is cleared or reviewed. Do not commit raw consent forms, names, contact details, or unlicensed text.

| Field | Required | Description |
|---|---|---|
| example_id | yes | Stable non-identifying identifier |
| source_id | yes | Pseudonymous source/song grouping key |
| speaker_id | yes | Pseudonymous speaker grouping key; use a stable project-specific token |
| text | yes, after clearance | Short excerpt or speaker-authored example permitted for storage |
| reference_label | yes | `sn`, `nd`, `zu`, `en`, `mul`, `und`, or another documented label |
| mixed_spans | when mixed | Character/token spans with language labels and boundary uncertainty |
| source_type | yes | Speaker-authored, licensed corpus, or other documented permitted source |
| rights_reference | yes | License/permission record reference, stored securely |
| permitted_use | yes | Explicit evaluation/storage scope |
| consent_reference | when consent-based | Opaque reference to external, access-controlled consent record |
| reviewer_1_label | yes | Independent first label |
| reviewer_2_label | yes | Independent second label |
| reviewer_expertise | yes | Minimal non-identifying evidence of language/variety expertise |
| annotation_date | yes | ISO date |
| adjudication_status | yes | pending, agreed, adjudicated, or unresolved |
| uncertainty_notes | when needed | Ambiguity, spelling variation, shared vocabulary, or insufficient context |
| split | yes | train, development, or test; assign after source/speaker grouping |
| publication_approved | yes | Explicit steward decision for this exact text and repository |

## Example empty record

Do not copy placeholder values into a benchmark. Populate only after permissions and review are real.

```json
{
  "example_id": "",
  "source_id": "",
  "speaker_id": "",
  "text": "",
  "reference_label": "",
  "mixed_spans": [],
  "source_type": "",
  "rights_reference": "",
  "permitted_use": "",
  "consent_reference": "",
  "reviewer_1_label": "",
  "reviewer_2_label": "",
  "reviewer_expertise": "",
  "annotation_date": "",
  "adjudication_status": "pending",
  "uncertainty_notes": "",
  "split": "",
  "publication_approved": false
}
```

The existing public corpus validator has its own versioned JSON schema. Convert only approved records into that schema after governance review; do not weaken the validator to accommodate incomplete metadata.
