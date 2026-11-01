# Confidence-aware streaming language timeline

The helper `tools/language_timeline.py` consumes timestamped segment records emitted
by the lyric engine and produces a review-oriented timeline. It preserves each
segment's original language, confidence signal, method, text, and time interval;
adds a candidate transition when adjacent segment labels change; and flags
unknown/mixed, short, missing-confidence, or low-confidence segments for human
review. It does not rewrite the underlying transcript or smooth away possible
code-switch boundaries.

Timestamp intervals and confidence thresholds must be finite numeric values.
A transition is marked for review when either adjacent segment requires review,
so a confident new label does not conceal uncertainty in the segment before it.

Example integration:

```python
from tools.language_timeline import build_language_timeline

timeline = build_language_timeline(streamed_segments, min_confidence=0.55)
```

Confidence values are model/heuristic signals, **not calibrated probabilities**
unless separately validated. The default threshold is a conservative review
trigger, not a measured operating point. Keep source timestamps and ASR metadata
alongside the timeline, and review uncertain transcriptions before publication.


The live JSONL event stream uses the same segment-review policy for both sides of a
candidate transition. This avoids a high-confidence new segment masking an uncertain
preceding segment. Every observed label change remains a candidate; rapid changes are
not silently smoothed away. Long timestamp gaps are preserved as gaps, not interpolated.


Segments retain separate ASR and lexical language evidence. When both signals name a
known but different language, the engine preserves both values and adds the
`asr_lexical_disagreement` review reason instead of silently choosing one as certain.
The disagreement may reflect code-switching or an error in either signal; it is a
review trigger, not a claim that either detector is correct.
