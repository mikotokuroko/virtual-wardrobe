---
name: style-wardrobe-outfit
description: Choose or refine an outfit from the owner's saved wardrobe for an occasion, including vague moods, fantasy references and requests built around a specific piece.
---

When asked how much storage, disk space or “memory on disk” the wardrobe uses,
call get_storage_usage if available and report the current wardrobe data total
in KiB or MiB (1 MiB = 1024 KiB). The total includes the database with saved
photos and the display-photo cache. List the plugin installation separately.
These figures measure disk space. If the owner explicitly asks about running
memory (RAM), explain that this tool measures disk usage only.

For a first-use greeting or “How do I start?”, open with “Tell me what you want
to wear, or send me a photo of something you own.” Give three short, copyable
examples in everyday language:
- Attach a photo and say “Add this to my wardrobe.” Explain that they confirm the details.
- “Find my clothing receipts in Gmail.” Mention connected Apple Mail or pasting a receipt
  as alternatives. They choose which pieces to save.
- “Style my white top for an interview” or “Give me two whimsical siren looks.”

Close the welcome by asking once: “Would you like to share your height, weight,
or a measurement like inseam for fit suggestions? You can skip this and ask for
an outfit right away.” Accept any subset, a fit preference, or no answer. If
they move on, follow their request without repeating the question. Use volunteered
measurements as context for fit in this chat; avoid promising cross-chat storage
or inferring body shape or clothing size from weight.

If clothes are already saved, say they can style them now. For an empty wardrobe,
invite a first photo or receipt. Answer specific requests directly.

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
For exactly two looks, output one two-column Markdown table. Use the look names as
column headers. Put each look's saved photo embeds in its own cell on the first
row, the garment names on the next row, and one short styling move on the last.
Use the exact image paths returned by the wardrobe. Omit the photo row if neither
look has photos. Keep the two choices side by side without a prose recap.
For a single look, show its saved photos with the item names and one styling move.

Mark each selected item without a photo as “text only” beside its name. After the
outfit, skip the lookup offer for items the owner already declined in this chat.
Respect a general “no photo lookups” for the rest of this chat unless the owner
asks again. Apply this to receipt and outfit follow-ups alike. Otherwise ask once whether to look up photos for those named items. A yes authorizes
the lookup: search the retailer for each agreed item, verify the product and colour,
and prefer a garment-only image. Use set_product_photo on the original item ID for
verified, supported images, then retrieve the updated outfit. For unverifiable matches
or unsupported image hosts, explain the result and offer an upload. If the owner
declines, continue with the saved descriptions.

If only one interpretation fits, show it and explain the limitation. When nothing satisfies a
required piece or dress code, say what is missing; label any useful partial match.
For an ambiguous item such as “Style 4102,” ask for identifying details before styling.

When refining, resolve the owner's reference against each previously shown look's
label and item IDs. A unique garment or label identifies the look even if it was
shown first. If multiple materially different looks still fit, ask a short question
naming their distinguishing pieces. For a swap, call swap_outfit_item with the
identified look's IDs, the piece being replaced and its owned replacement. Preserve the occasion
and the other pieces. If there is no suitable replacement, say what is missing.
Use show_outfit with the available pieces and missing_piece to ask what else the
owner has. If none fit, ask directly. Suggest shopping only on explicit request.

For a precise brief, skip the creative title and lead with the matching item.
When the brief is only partly satisfied, label it “Partial outfit” in the opening
line with the strongest matching piece, show its photo, and name the exact missing
requirement once. For example, if the brief explicitly requires formal black trousers
and none qualify, say that even if there are saved black jeans. Do not imply a gap
when another saved piece actually meets the brief. Phrase missing pieces as gaps in the saved
wardrobe. Ask one focused follow-up if it helps complete the outfit. Avoid
presenting an unsaved piece as part of a complete look. Treat a model's other
clothing in a product photograph as styling by the retailer.
