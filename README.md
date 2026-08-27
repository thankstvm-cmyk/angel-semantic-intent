# angel-semantic-intent
Semantic Intent Classification System for Angel - Transforms Angel from keyword-based to intelligent semantic understanding

## Greeting classifier behavior

Angel now runs a dedicated semantic greeting classifier before the normal intent lookup and fallback flow.

- Class priority: `greeting_plus_task` → `wellbeing_query` → `time_greeting` → `basic_greeting` → `farewell` → `non_greeting`
- Normalization includes lowercase cleanup, punctuation trimming, repeated-letter collapse, typo folding such as `hellow` → `hello`, `gud` → `good`, `after noon` → `afternoon`, `mornin` → `morning`, and `hw r u` → `how are you`
- Confidence thresholds:
  - `>= 0.75` high: auto-route
  - `0.50–0.74` medium: safe route with short confirmation when needed
  - `< 0.50` low: treat as `non_greeting`
- Greeting-only classes return a natural response without using the external lookup fallback
- `greeting_plus_task` strips the greeting, hands the remaining request to the existing task pipeline, blocks dead-end fallback phrases, and appends: `Would you like suggestions regarding this topic?`
