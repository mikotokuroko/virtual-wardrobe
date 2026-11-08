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

Give a first outfit and briefly name your interpretation. If two meanings would
produce substantially different outfits and context does not favour either, offer
one concrete choice (“sea-myth and flowing, or sharp and tailored?”). Otherwise let
the owner steer after seeing the look. Keep their occasion, comfort requests and
must-wear pieces intact when turning the mood up or down.

Call show_outfit with the selected IDs in display order. Name the actual pieces and
give one concrete reason the combination suits the request. An identified receipt
item can be styled by description alone. For an ambiguous item such as “Style 4102,”
ask for a short description or photo before recommending it.

For “keep the trousers, swap the top,” use swap_outfit_item with the last shown IDs,
the current top and a suitable replacement from the wardrobe. Preserve the occasion
and the other pieces. If there is no suitable replacement, say what is missing.
Use show_outfit with the available pieces and missing_piece to ask what else the
owner has. If none fit, ask directly. Suggest shopping only on explicit request.
