---
trigger: always_on
description: Ask the user before making ambiguous or preference-dependent choices, and pause at phase gates
---

# Ask Before Assuming

- Never silently assume the user's intended choice when multiple reasonable options exist.
- When a decision materially affects the result and the user's preference is unknown, ask the user before proceeding.
- Pause at every phase gate defined in `.agents/initial-plan.md`. Do not start the next phase until the user says to.

## How You Ask

- Present available options as a numbered list or selectable choices whenever the interface supports it.
- For each option, briefly explain what it means, why someone might choose it, and its trade-offs.
- Include a recommended option when appropriate, explaining why you recommend it.
- Clearly distinguish facts from assumptions and recommendations.
- Do not ask unnecessary questions when the user has already specified the answer or when the choice has no meaningful impact.
- If clarification is required, pause the affected work until the user responds.
