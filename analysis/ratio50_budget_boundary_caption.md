# Ratio50 Budget Boundary Figure Caption

Figure: Future-Seed gain on the frozen `ratio50` video line as a function of training budget.

- Strictly matched evidence is shown for `90` and `120` steps, where task, model, mask, and eval cadence are identical across 3 seeds.
- Supporting evidence is shown for `60` and `150` steps, where the task line is the same but eval details differ slightly.
- The key result is a boundary transition:
  - `90` steps: no measurable gain
  - `120` steps: stable positive gain
  - `150` steps: larger positive gain

Supported takeaway:
Future-Seed does not help in the low-budget regime on this task, but produces repeatable foreground recovery gains once the budget crosses roughly `120` steps.
