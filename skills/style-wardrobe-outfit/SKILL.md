---
name: style-wardrobe-outfit
description: Choose or refine an outfit from the owner's saved wardrobe for an occasion, including vague moods, fantasy references and requests built around a specific piece.
---

Use list_items to see what the owner has. Start with any piece they asked to wear.
Choose the remaining pieces for their occasion, dress code and stated preferences.
Use the recorded colours, cuts and fabrics to judge how the pieces work together.
For example, for dinner around green trousers, choose a suitable owned top and add
an accessory if it helps the look. Use show_item if a photo would settle a choice.

When someone names a feeling, treat it as a styling brief. Use the rest of their
words to narrow its meaning. “Whimsical, like a siren from a fantasy story” points
toward an ocean myth; “siren for the office” suggests a different silhouette.
Check the wardrobe before asking for more detail. Choose two or three visible cues
that can carry the mood: how fabric moves, the outline of the outfit, an unexpected
proportion, or the way an accessory catches light. Verify these features in the saved
description or photo. A styling suggestion such as tying a scarf low at the hip can
supply the cue even when the clothes are ordinary.

Let the owner's requested number of looks take priority. Otherwise use these defaults:

- For an open-ended mood such as “whimsical” or “I want to feel like fantasy,”
  use the canvas-design idea of contrasting visual compositions. Show two distinct
  interpretations in the same reply when the wardrobe supports both. Give each a
  short visual label. Use a different silhouette, texture, accent or styling
  treatment so the choice is visible. The owner can pick a direction after seeing both.
- For a concrete brief such as “formal interview outfit with a white top,” show
  the single strongest match. Honour the requested top and dress code. Give
  additional options when the owner asks. A mood word within an otherwise specific
  brief does not by itself call for two looks.

For each look call show_outfit with the owner's selected item IDs in display order.
Present the returned wardrobe photos under that look's label, with one brief styling
note. Use only those stored photos as visuals, including for fantasy prompts.
If an identified receipt item has no photo, label it as text-only. If only one
interpretation fits, show it and explain the limitation. When nothing satisfies a
required piece or dress code, say what is missing; label any useful partial match.
For an ambiguous item such as “Style 4102,” ask for identifying details before styling.

For “keep the trousers, swap the top,” use swap_outfit_item with the last shown IDs,
the current top and a suitable replacement from the wardrobe. Preserve the occasion
and the other pieces. If there is no suitable replacement, say what is missing.
Use show_outfit with the available pieces and missing_piece to ask what else the
owner has. If none fit, ask directly. Suggest shopping only on explicit request.
