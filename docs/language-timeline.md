# Confidence-aware streaming language timeline

The helper `tools/language_timeline.py` consumes timestamped segment records emitted
by the lyric engine and produces a review-oriented timeline. It preserves each
segment's original language, confidence signal, method, text, and time interval;
adds a candidate transition when adjacent segment labels change; and flags
unknown/mixed, short, missing-confidence, or low-confidence segments for human
review. It does not rewrite the underlying transcript or smooth away possible
code-switch boundaries.

Example integration:

```python
from tools.language_timeline import build_language_timeline

timeline = build_language_timeline(streamed_segments, min_confidence=0.55)
```

Confidence values are model/heuristic signals, **not calibrated probabilities**
unless separately validated. The default threshold is a conservative review
trigger, not a measured operating point. Keep source timestamps and ASR metadata
alongside the timeline, and review uncertain transcriptions before publication.
